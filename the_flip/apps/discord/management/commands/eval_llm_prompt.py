"""Evaluate LLM prompt against test fixtures.

This command runs the Discord bot's LLM classifier against curated test
fixtures to measure prompt accuracy. Use this to iterate on prompts without
modifying production code.

Usage:
    python manage.py eval_llm_prompt              # Run all fixtures
    python manage.py eval_llm_prompt --prompt-file /tmp/new_prompt.txt
    python manage.py eval_llm_prompt --verbose    # Show all results
    python manage.py eval_llm_prompt --output results.json
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from asgiref.sync import sync_to_async
from constance import config
from django.core.management.base import BaseCommand, CommandError

from the_flip.apps.catalog.models import MachineInstance
from the_flip.apps.discord.llm import (
    SYSTEM_PROMPT,
    RecordSuggestion,
    _build_user_message,
    _call_anthropic,
    _parse_tool_response,
)
from the_flip.apps.discord.llm_eval_fixtures import (
    ALL_FIXTURES,
    ExpectedSuggestion,
    LLMTestCase,
)

# Estimated cost per API call (Claude Sonnet, ~1k input + 1k output tokens)
ESTIMATED_COST_PER_CALL = 0.003


@dataclass
class SuggestionKey:
    """Hashable key for comparing suggestions."""

    record_type: str
    machine_slug: str

    def __hash__(self):
        return hash((self.record_type, self.machine_slug))

    def __eq__(self, other):
        if not isinstance(other, SuggestionKey):
            return False
        return self.record_type == other.record_type and self.machine_slug == other.machine_slug


@dataclass
class FixtureResult:
    """Result of evaluating a single fixture."""

    fixture_id: str
    passed: bool
    expected: list[ExpectedSuggestion]
    actual: list[RecordSuggestion]
    correct: list[SuggestionKey]  # In both expected and actual
    missing: list[SuggestionKey]  # In expected but not actual
    extra: list[SuggestionKey]  # In actual but not expected
    error: str | None = None


@dataclass
class EvalResults:
    """Aggregated evaluation results."""

    prompt_source: str
    prompt_hash: str
    timestamp: str
    fixture_results: list[FixtureResult]
    parts_enabled: bool

    @property
    def total(self) -> int:
        return len(self.fixture_results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.fixture_results if r.passed)

    @property
    def accuracy(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0


class Command(BaseCommand):
    help = "Evaluate LLM prompt against test fixtures"

    def add_arguments(self, parser):
        parser.add_argument(
            "--prompt-file",
            "-p",
            type=str,
            help="Path to alternate prompt file to test",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show all results, not just failures",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            help="Export results to JSON file",
        )
        parser.add_argument(
            "--fixture",
            "-f",
            type=str,
            help="Run only a specific fixture by name",
        )
        parser.add_argument(
            "--model",
            "-m",
            type=str,
            help="Override model (e.g., claude-opus-4-20250514)",
        )

    def handle(self, *args, **options):
        asyncio.run(self._async_handle(options))

    async def _async_handle(self, options):
        # Check API key
        api_key = await self._get_api_key()
        if not api_key:
            raise CommandError(
                "ANTHROPIC_API_KEY not configured in Constance settings.\n"
                "Set it in Django admin: /admin/constance/config/"
            )

        # Check parts enabled
        parts_enabled = await self._get_parts_enabled()

        # Get prompt
        prompt_source, system_prompt = self._get_prompt(options.get("prompt_file"))
        prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()[:12]

        # Get fixtures
        fixtures = self._get_fixtures(parts_enabled, options.get("fixture"))
        if not fixtures:
            raise CommandError("No fixtures to run")

        # Get machines
        machines = await self._get_machines()

        # Validate fixture machine slugs exist in database
        self._validate_fixture_machines(fixtures, machines)

        # Run evaluation
        model = options.get("model")
        self.stdout.write(f"\nRunning {len(fixtures)} fixtures...")
        results = await self._run_evaluation(
            fixtures=fixtures,
            machines=machines,
            api_key=api_key,
            system_prompt=system_prompt,
            prompt_source=prompt_source,
            prompt_hash=prompt_hash,
            parts_enabled=parts_enabled,
            model=model,
        )

        # Display results
        self._display_results(results, options.get("verbose", False))

        # Export if requested
        if options.get("output"):
            self._export_results(results, options["output"])

    @sync_to_async
    def _get_api_key(self) -> str:
        return config.ANTHROPIC_API_KEY

    @sync_to_async
    def _get_parts_enabled(self) -> bool:
        return config.PARTS_ENABLED

    @sync_to_async
    def _get_machines(self) -> list[dict]:
        machines = MachineInstance.objects.order_by("slug")
        return [{"slug": m.slug, "name": m.name} for m in machines]

    def _get_prompt(self, prompt_file: str | None) -> tuple[str, str]:
        """Return (source_description, prompt_text)."""
        if prompt_file:
            path = Path(prompt_file)
            if not path.exists():
                raise CommandError(f"Prompt file not found: {prompt_file}")
            return (str(path), path.read_text())
        return ("llm.py:SYSTEM_PROMPT", SYSTEM_PROMPT)

    def _get_fixtures(
        self, parts_enabled: bool, fixture_name: str | None = None
    ) -> dict[str, LLMTestCase]:
        """Get fixtures to run, filtering by parts setting and optional name."""
        fixtures = ALL_FIXTURES.copy()

        # Filter to specific fixture if requested
        if fixture_name:
            if fixture_name not in fixtures:
                available = ", ".join(sorted(fixtures.keys()))
                raise CommandError(f"Fixture '{fixture_name}' not found.\nAvailable: {available}")
            fixtures = {fixture_name: fixtures[fixture_name]}

        # Filter out part_request fixtures if parts disabled
        if not parts_enabled:
            fixtures = {
                name: f
                for name, f in fixtures.items()
                if not any(e.record_type == "part_request" for e in f.expected)
            }

        return fixtures

    def _validate_fixture_machines(
        self, fixtures: dict[str, LLMTestCase], machines: list[dict]
    ) -> None:
        """Validate all fixture machine slugs exist in database."""
        db_slugs = {m["slug"] for m in machines}
        fixture_slugs = {e.machine_slug for f in fixtures.values() for e in f.expected}
        missing = fixture_slugs - db_slugs

        if missing:
            self.stdout.write(self.style.ERROR("\nMissing machines in database:"))
            for slug in sorted(missing):
                self.stdout.write(f"  {slug}")
            raise CommandError(
                "Fixtures reference machines not in database. "
                "Add the missing machines or run 'make sample-data'."
            )

    async def _run_evaluation(
        self,
        fixtures: dict[str, LLMTestCase],
        machines: list[dict],
        api_key: str,
        system_prompt: str,
        prompt_source: str,
        prompt_hash: str,
        parts_enabled: bool,
        model: str | None = None,
    ) -> EvalResults:
        """Run all fixtures and collect results."""
        fixture_results = []

        for i, (fixture_id, fixture) in enumerate(fixtures.items(), 1):
            self.stdout.write(f"  [{i}/{len(fixtures)}] {fixture_id}...", ending="")
            self.stdout.flush()

            result = await self._evaluate_fixture(
                fixture_id=fixture_id,
                fixture=fixture,
                machines=machines,
                api_key=api_key,
                system_prompt=system_prompt,
                model=model,
            )
            fixture_results.append(result)

            if result.error:
                self.stdout.write(self.style.ERROR(" ERROR"))
            elif result.passed:
                self.stdout.write(self.style.SUCCESS(" PASS"))
            else:
                self.stdout.write(self.style.ERROR(" FAIL"))

        return EvalResults(
            prompt_source=prompt_source,
            prompt_hash=prompt_hash,
            timestamp=datetime.now().isoformat(),
            fixture_results=fixture_results,
            parts_enabled=parts_enabled,
        )

    async def _evaluate_fixture(
        self,
        fixture_id: str,
        fixture: LLMTestCase,
        machines: list[dict],
        api_key: str,
        system_prompt: str,
        model: str | None = None,
    ) -> FixtureResult:
        """Evaluate a single fixture."""
        try:
            # Build user message
            user_message = _build_user_message(fixture.to_context(), machines)

            # Call API
            response = await _call_anthropic(api_key, user_message, system_prompt, model)

            # Parse response
            suggestions = _parse_tool_response(response)

            # Compare
            correct, missing, extra = self._compare_suggestions(
                expected=fixture.expected,
                actual=suggestions,
            )

            passed = len(missing) == 0 and len(extra) == 0

            return FixtureResult(
                fixture_id=fixture_id,
                passed=passed,
                expected=fixture.expected,
                actual=suggestions,
                correct=correct,
                missing=missing,
                extra=extra,
            )

        except Exception as e:
            return FixtureResult(
                fixture_id=fixture_id,
                passed=False,
                expected=fixture.expected,
                actual=[],
                correct=[],
                missing=[],
                extra=[],
                error=str(e),
            )

    def _compare_suggestions(
        self,
        expected: list[ExpectedSuggestion],
        actual: list[RecordSuggestion],
    ) -> tuple[list[SuggestionKey], list[SuggestionKey], list[SuggestionKey]]:
        """Compare expected vs actual using multiset comparison.

        Returns (correct, missing, extra) where:
        - correct: suggestions that match between expected and actual
        - missing: expected but not in actual
        - extra: in actual but not expected
        """
        expected_keys = [SuggestionKey(e.record_type, e.machine_slug) for e in expected]
        actual_keys = [SuggestionKey(a.record_type, a.machine_slug) for a in actual]

        expected_counter = Counter(expected_keys)
        actual_counter = Counter(actual_keys)

        correct = []
        missing = []
        extra = []

        # Find correct and missing
        for key, expected_count in expected_counter.items():
            actual_count = actual_counter.get(key, 0)
            match_count = min(expected_count, actual_count)
            correct.extend([key] * match_count)
            missing.extend([key] * (expected_count - match_count))

        # Find extra
        for key, actual_count in actual_counter.items():
            expected_count = expected_counter.get(key, 0)
            extra_count = max(0, actual_count - expected_count)
            extra.extend([key] * extra_count)

        return correct, missing, extra

    def _display_results(self, results: EvalResults, verbose: bool):
        """Display evaluation results."""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("LLM Prompt Evaluation Results")
        self.stdout.write("=" * 60)

        self.stdout.write(f"\nPrompt: {results.prompt_source} (sha256: {results.prompt_hash})")
        self.stdout.write(f"Timestamp: {results.timestamp}")

        # Overall accuracy
        accuracy_pct = results.accuracy * 100
        if results.accuracy >= 0.9:
            style = self.style.SUCCESS
        elif results.accuracy >= 0.7:
            style = self.style.WARNING
        else:
            style = self.style.ERROR
        self.stdout.write(
            style(f"\nOverall: {accuracy_pct:.1f}% ({results.passed}/{results.total} correct)")
        )

        # By record type
        self._display_by_record_type(results)

        # Failures
        failures = [r for r in results.fixture_results if not r.passed]
        if failures:
            self.stdout.write("\n" + "-" * 60)
            self.stdout.write("Failures")
            self.stdout.write("-" * 60)
            for result in failures:
                self._display_failure(result)

        # Verbose: show passes too
        if verbose:
            passes = [r for r in results.fixture_results if r.passed]
            if passes:
                self.stdout.write("\n" + "-" * 60)
                self.stdout.write("Passes")
                self.stdout.write("-" * 60)
                for result in passes:
                    self._display_pass(result)

        # Run summary at the end
        estimated_cost = results.total * ESTIMATED_COST_PER_CALL
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(f"Fixtures: {results.total}")
        self.stdout.write(f"Estimated cost: ${estimated_cost:.3f}")

    def _display_by_record_type(self, results: EvalResults):
        """Display accuracy by record type."""
        self.stdout.write("\nBy Record Type:")

        # Gather all expected suggestions across fixtures
        type_stats: dict[str, dict[str, int]] = {}
        for result in results.fixture_results:
            for exp in result.expected:
                if exp.record_type not in type_stats:
                    type_stats[exp.record_type] = {"total": 0, "correct": 0}
                type_stats[exp.record_type]["total"] += 1

            for correct in result.correct:
                if correct.record_type in type_stats:
                    type_stats[correct.record_type]["correct"] += 1

        for record_type in sorted(type_stats.keys()):
            stats = type_stats[record_type]
            pct = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
            self.stdout.write(
                f"  {record_type:20} {pct:5.1f}% ({stats['correct']}/{stats['total']})"
            )

    def _display_failure(self, result: FixtureResult):
        """Display a single failure."""
        self.stdout.write(self.style.ERROR(f"\n[FAIL] {result.fixture_id}"))

        if result.error:
            self.stdout.write(f"  Error: {result.error}")
            return

        if result.missing:
            self.stdout.write("  Missing:")
            for key in result.missing:
                self.stdout.write(f"    - {key.record_type} for {key.machine_slug}")

        if result.extra:
            self.stdout.write("  Extra:")
            for key in result.extra:
                self.stdout.write(f"    + {key.record_type} for {key.machine_slug}")

    def _display_pass(self, result: FixtureResult):
        """Display a single pass (for verbose mode)."""
        self.stdout.write(self.style.SUCCESS(f"\n[PASS] {result.fixture_id}"))
        if result.correct:
            for key in result.correct:
                self.stdout.write(f"    {key.record_type} for {key.machine_slug}")

    def _export_results(self, results: EvalResults, output_path: str):
        """Export results to JSON."""
        data = {
            "prompt_source": results.prompt_source,
            "prompt_hash": results.prompt_hash,
            "timestamp": results.timestamp,
            "parts_enabled": results.parts_enabled,
            "summary": {
                "total": results.total,
                "passed": results.passed,
                "accuracy": results.accuracy,
            },
            "fixtures": [
                {
                    "id": r.fixture_id,
                    "passed": r.passed,
                    "error": r.error,
                    "expected": [asdict(e) for e in r.expected],
                    "actual": [
                        {"record_type": a.record_type, "machine_slug": a.machine_slug}
                        for a in r.actual
                    ],
                    "missing": [
                        {"record_type": k.record_type, "machine_slug": k.machine_slug}
                        for k in r.missing
                    ],
                    "extra": [
                        {"record_type": k.record_type, "machine_slug": k.machine_slug}
                        for k in r.extra
                    ],
                }
                for r in results.fixture_results
            ],
        }

        path = Path(output_path)
        path.write_text(json.dumps(data, indent=2))
        self.stdout.write(f"\nResults exported to: {path}")
