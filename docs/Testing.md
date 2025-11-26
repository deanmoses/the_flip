# Automated Testing Guide

This is a guide for developers and AI assistants around running and creating automated tests.

## Running Tests

```bash
make test              # Run full test suite
```

### Running Tests by Tag

Tests are tagged by category for selective execution:

```bash
# Run only model tests (fast, no HTTP)
python manage.py test --tag=models

# Run only API/AJAX endpoint tests
python manage.py test --tag=api

# Run only view tests
python manage.py test --tag=views

# Run unit tests (no external dependencies)
python manage.py test --tag=unit

# Run integration tests (may need ffmpeg, etc.)
python manage.py test --tag=integration

# Exclude slow tests
python manage.py test --exclude-tag=integration
```

Available tags:
- `models` - Model unit tests
- `forms` - Form validation tests
- `views` - View/HTTP tests
- `api` - JSON API endpoint tests
- `ajax` - AJAX endpoint tests
- `admin` - Django admin tests
- `auth` - Authentication tests
- `registration` - Registration flow tests
- `terminals` - Shared terminal account tests
- `public` - Public-facing (no auth) tests
- `unit` - Fast unit tests
- `integration` - Integration tests (may need external tools)
- `environment` - Environment/dependency checks
- `tasks` - Background task tests

## Suite Layout

Tests are organized in test packages within each app:

```
the_flip/apps/
├── accounts/
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py      # Maintainer, Invitation models
│       ├── test_registration.py # Registration flows
│       ├── test_profile.py     # Profile & password views
│       ├── test_terminals.py   # Shared terminal accounts
│       ├── test_admin.py       # Admin interface
│       └── test_navigation.py  # Navigation UI
├── catalog/
│   └── tests.py                # Machine model/instance tests
├── core/
│   ├── tests.py                # Template tag tests
│   └── test_utils.py           # Shared test factories & mixins
└── maintenance/
    └── tests/
        ├── __init__.py
        ├── test_problem_reports.py  # Problem report CRUD
        ├── test_log_entries.py      # Log entry CRUD
        ├── test_api.py              # API endpoints
        ├── test_tasks.py            # Background tasks (with mocking examples)
        └── test_environment.py      # FFmpeg availability checks
```

## Test Utilities

Use the shared test utilities in `the_flip.apps.core.test_utils` to reduce boilerplate:

### Factory Functions

```python
from the_flip.apps.core.test_utils import (
    create_user,
    create_staff_user,
    create_superuser,
    create_machine_model,
    create_machine,
    create_problem_report,
    create_log_entry,
    create_shared_terminal,
)

# Create test data with sensible defaults
user = create_staff_user()  # Auto-generates username
machine = create_machine()  # Creates model + instance
report = create_problem_report(machine=machine)

# Or customize as needed
user = create_staff_user(
    username="alice",
    first_name="Alice",
    last_name="Smith",
)
```

### Test Mixins

```python
from django.test import TestCase
from the_flip.apps.core.test_utils import TestDataMixin, AuthenticatedTestMixin

class MyTestCase(TestDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        # Now available: self.machine, self.staff_user, self.regular_user, etc.

class MyAuthenticatedTestCase(AuthenticatedTestMixin, TestDataMixin, TestCase):
    def test_something(self):
        # Already logged in as self.staff_user
        response = self.client.get('/some-staff-url/')
```

## Mocking Patterns

For tests that need to mock external dependencies, see examples in `test_tasks.py`:

```python
from unittest.mock import patch, MagicMock

# Mock subprocess calls (e.g., ffmpeg)
@patch("subprocess.run")
def test_ffmpeg_called(self, mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    # ... test code ...
    mock_run.assert_called_once()

# Mock HTTP requests
@patch("requests.post")
def test_upload(self, mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    # ... test code ...

# Override Django settings
from django.test import override_settings

@override_settings(RATE_LIMIT_REPORTS_PER_IP=1)
def test_stricter_rate_limit(self):
    # ... test with modified setting ...

# Mock time
@patch("django.utils.timezone.now")
def test_with_frozen_time(self, mock_now):
    mock_now.return_value = datetime(2024, 6, 15, tzinfo=timezone.utc)
    # ... test time-dependent code ...
```

## Writing New Tests

When adding new tests:

1. **Choose the right file** - Place tests in the appropriate `test_*.py` file by domain
2. **Add tags** - Tag tests appropriately for selective execution:
   ```python
   from django.test import TestCase, tag

   @tag("views", "api")
   class MyAPITests(TestCase):
       ...
   ```
3. **Use factories** - Prefer `create_*` functions over manual object creation
4. **Keep tests independent** - Each test should set up its own data
5. **Use mixins for common setup** - Extend `TestDataMixin` for standard test data

## Coverage

Prioritize highest-value flows:
1. **Domain models & business rules:** Core data behaviors, status transitions, and queryset/helpers should always have regression coverage.
2. **Forms & public views:** Anything that processes user input (especially rate-limiting or privacy-sensitive code) needs targeted tests.
3. **Authenticated workflows:** Staff-only dashboards, status updates, and permissions should have tests using authenticated users.
4. **APIs or integrations:** When new endpoints are added, cover success and failure cases.

End-to-end browser coverage is intentionally out of scope right now to keep the suite fast.
