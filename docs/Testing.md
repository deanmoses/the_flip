# Automated Testing Guide

This is a guide for developers and AI assistants around running and creating automated tests.

## 1. Scaffolding Reference

When bootstrapping or reconfiguring the test harness, follow [`scaffolding/Testing_Scaffold.md`](scaffolding/Testing_Scaffold.md). It captures the base settings module, directory layout, and CI hooks that every regenerated project should preserve.

## 2. Framework & Tooling
- **Test runner:** Use Django's built-in runner (`python manage.py test`). It is the most widely supported path for Django projects.
- **Base classes:** Prefer `django.test.TestCase`, `TransactionTestCase`, and Django's `Client` for integration-style checks. These give you database isolation and fixtures without extra dependencies.
- **No Selenium / browser automation:** Keep the suite lightweight and fast. Feature coverage that would require browser automation should be expressed as form/view tests using the Django test client.

## 3. Current Suite Layout
All automated tests live under each app’s `tests/` package and follow Django's discovery rules (`test_*.py`, `Test*` classes). Existing coverage touches core models, form/view logic, and integration tests for critical status transitions.


When adding new tests:
1. Place them in the app-specific `tests/` package next to the feature being exercised.
2. Name files and classes with clear intent (`test_views_dashboard.py`, `AssignmentWorkflowTests`, etc.).
3. Keep each test independent by creating its own data in `setUp()` or factory helpers.

## 4. Running Tests Locally
From the repo root:

```bash
make test           # runs the entire suite
```

Tips:
- `make test` handles activating the virtual environment and setting the correct Django settings module
- To scope to a single module: `DJANGO_SETTINGS_MODULE=the_flip.settings.test .venv/bin/python manage.py test app.tests.test_feature`
- Tests rely on the default SQLite database that Django creates in memory; no extra services or env vars are required.
- If you add dependencies for tests, ensure they land in `requirements.txt`.

## 5. When to Run Tests
- **Before opening or updating a PR:** CI will run tests automatically, but running locally first keeps reviews fast and reduces deploy blockers.
- **During development:** Run tests frequently to catch issues early.

## 6. Coverage Expectations
This is still a prototype headed toward v1, so prioritize the highest-value flows:
1. **Domain models & business rules:** Core data behaviors, status transitions, and queryset/helpers should always have regression coverage.
2. **Forms & public views:** Anything that processes user input (especially rate-limiting or privacy-sensitive code) needs targeted tests.
3. **Authenticated workflows:** Staff-only dashboards, status updates, and permissions should have tests using authenticated users.
4. **APIs or integrations:** When new endpoints are added, cover success and failure cases; use Django's test client or `APIClient` if DRF enters the stack.

End-to-end browser coverage is intentionally out of scope right now to keep the suite fast. If we later need smoke tests, consider lightweight HTTP checks or component-level tests before introducing heavier tooling.

## 7. Continuous Integration

GitHub Actions automatically runs tests on all pull requests and pushes to `main`. The CI workflow:
- Runs the full test suite with `python manage.py test`
- Uses Python 3.13 and PostgreSQL 15 to match production
- Installs system dependencies (FFmpeg, libheif) from `nixpacks.toml`
- Optionally runs linting (`make lint`) and type checking (`make typecheck`)

See [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) for the complete configuration.

## 8. Future Enhancements
- Add code coverage reporting (`coverage.py`) once the suite grows, but keep it optional until we stabilize v1.
