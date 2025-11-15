# Django & Python Generation Guide

This document contains instructions for AI assistants generating the project’s Django and Python. 

It distills standard, boring-best-practice Django and Python habits so the output stays clear, maintainable, and pleasant for both humans and future AI iterations.

## Goals & Principles

- **Prefer the conventional solution** over clever abstractions. Follow Django docs, PEP 8/PEP 257, and keep code self-explanatory.
- **Keep responsibilities focused**: each module should do one thing well (models define data, forms validate/persist, views orchestrate HTTP).
- **Bias toward readability** by naming things explicitly, writing docstrings that describe why, and using type hints where they provide clarity.
- **Optimize for future edits**: avoid hidden coupling, keep side effects local, and document expectations in tests.

## Project Organization

- Follow the structure documented in `docs/Project_Structure.md`: multiple apps grouped by domain.
- Each app should keep the standard files (`models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`, `tests/`, `templates/<app>/`, `management/commands/`), splitting further into packages when modules get large (e.g., `maintenance/models/task.py`).
- Store shared helpers (decorators, template tags, mixins) in the `core` app or clearly named utility modules. Never hide functionality inside `__init__.py`.

## Settings & Configuration

- Use layered settings modules (`settings/base.py`, `dev.py`, `test.py`, `prod.py`). Import `base` everywhere, override environment-specific values (databases, caches, logging, security) per file.
- Read secrets and environment-specific flags via `python-decouple` or `django-environ`. Never hardcode keys, passwords, or hostnames.
- Enable secure defaults in `prod.py`: `SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`, and WhiteNoise or CDN-backed static config.
- Keep `LOGGING` explicit so errors from AI-generated code land in log files or stdout for Heroku/Render.

## Models & Data Access

- Use descriptive fields with validators and `help_text`. Prefer numeric fields (`PositiveSmallIntegerField`) over string+regex combos when the data is numeric.
- Keep domain behavior close to the data. Custom `QuerySet`/manager methods encapsulate repeated filters (e.g., `TaskQuerySet.problem_reports()`, `MachineInstanceQuerySet.on_floor()`).
- Wrap multi-model updates in domain methods that enforce invariants (`Task.set_machine_status` updates both the task and the machine, creates a `LogEntry`, and runs inside `transaction.atomic()`).
- Leverage Django features before writing custom code: constraints (`UniqueConstraint`, `CheckConstraint`), database indexes, choices enums, `AutoSlugField` packages if helpful.
- Maintain forward-only migrations with descriptive names; avoid data migrations unless necessary and document each one’s purpose.

## Forms & Validation

- Use `ModelForm`s for CRUD flows; add `clean_*` methods for business rules and keep view logic simple.
- Build reusable widget mixins (e.g., `FormStyleMixin` that applies the classes defined in `docs/CSS_Generation_Guide.md`) instead of copy/pasting `attrs={'class': 'form-control'}`.
- Keep `__init__` overrides minimal. If a form depends on request context (current user, machine slug), accept those as keyword arguments, pop them, and document assumptions in docstrings.
- Always validate that the generated queryset matches current permissions (public visitors see only floor machines, maintainers see all). Tests should cover these cases.

## Views, URLs & Services

- Stick to standard routing: each app owns its own `urls.py`, included from the project `urls.py`. Keep path names stable and descriptive.
- Favor class-based views (`ListView`, `DetailView`, `FormView`) for CRUD or list/detail flows, but don’t hesitate to use function-based views when the logic reads clearer.
- Enforce access control through decorators/mixins (`login_required`, `permission_required`, or custom `MaintainerRequiredMixin`). Public endpoints should still validate input and CSRF tokens.
- Delegate complex operations to service/helper modules (e.g., `maintenance.services.task_creation`). Views gather request data, call services, and handle redirects/messages.
- Use Django’s pagination helpers and keep filter state in GET parameters so pages stay shareable.

## Templates & Static Assets

- Organize templates under `templates/<app>/`. Use app-specific base templates that extend a project-wide `base.html`.
- Keep HTML semantic, push repeated UI chunks into `include`s or template tags, and minimize inline CSS/JS. Reference shared CSS guidance in `docs/CSS_Generation_Guide.md`.
- Never expose private data (reporter contact info, IPs) in public templates. Add template tags to encapsulate privacy rules, and test them.
- Use the `{% static %}` and `{% url %}` tags everywhere; never hardcode paths.

## Admin, Commands & Utilities

- Register models in their native apps with tailored `ModelAdmin`s (search, filters, list display). Keep admin-only helpers under `admin.py` or `admin/` packages.
- Management commands live under `app/management/commands/` with clear names, docstrings, and friendly `self.stdout.write` output. Validate prerequisites before mutating data and wrap large imports in transactions.
- Custom decorators or template tags should import only what they need, catch specific exceptions, and log unexpected states instead of silent `except:` blocks.

## Testing & Quality

- Every model method, form, and view path gets test coverage. Prefer Django’s `TestCase` (database isolation) and `pytest` if the project adopts it.
- Write tests in the same app as the code they cover, using factories or helper functions for readability. Keep assertions focused on behavior (status codes, database changes, privacy rules).
- Run tests with the intended settings module (`DJANGO_SETTINGS_MODULE=the_flip.settings.test`). Keep CI scripts simple: `python -m compileall`, `python manage.py check`, `python manage.py test`.
- Use linting/formatting tools (`ruff`, `black`, `isort`) to enforce a consistent style that AI can mimic.

## Documentation & Communication

- When generating new modules, include docstrings summarizing intent and reference related docs (`Data_Model`, `Maintenance_Workflows`) when relevant.
- Update README and domain docs whenever behavior changes so humans and future AI runs have accurate context.
- Prefer explicit TODO comments over implied context; include the “why” so a later generation can safely finish or remove the item.

Adhering to these guidelines keeps regenerated Django projects predictable, secure, and easy to maintain—exactly what both humans and AI helpers need for long-term success.
