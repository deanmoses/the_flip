# Contributing to The Flip

This guide covers the contribution workflow, code quality standards, and testing requirements.

## Table of Contents

- [Getting Started](#getting-started)
- [Contributor Setup](#contributor-setup)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Branch Naming Convention](#branch-naming-convention)

## Getting Started

Before you begin:

1. **Follow the setup in [README.md](README.md)** - Get the app running locally first
2. **Review [docs/](docs/)** - Understand the architecture and conventions:
   - [Project Structure](docs/Project_Structure.md) - Directory layout and app organization
   - [Data Model](docs/Datamodel.md) - Database schema and relationships
   - [Django/Python](docs/Django_Python.md) - Coding conventions and patterns
   - [HTML/CSS](docs/HTML_CSS.md) - Frontend conventions
   - [Testing](docs/Testing.md) - Testing strategies

## Contributor Setup

After completing the basic setup in README.md, add these contributor tools:

### 1. Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

This installs:
- **ruff** - Fast linter and formatter
- **mypy** - Type checker
- **coverage** - Test coverage reporting
- **pre-commit** - Git hooks for automated checks

### 2. Install Pre-commit Hooks

```bash
pre-commit install
```

This automatically runs code quality checks before each commit. If checks fail, the commit is blocked until you fix the issues.

### 3. Install FFmpeg (for video features)

Required for testing video transcoding:
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `apt-get install ffmpeg`
- Windows: Download from [ffmpeg.org](https://ffmpeg.org/)

### 4. Run Background Worker (when testing videos)

Video transcoding requires the Django Q worker running:

```bash
# In a separate terminal
make runq
```

Without this, video uploads will queue but not process.

## Development Workflow

1. **Create a feature branch** (see [Branch Naming Convention](#branch-naming-convention) below)
2. **Make your changes** following the code quality guidelines
3. **Write tests** for new functionality
4. **Run tests** to ensure nothing breaks
5. **Commit your changes** with clear commit messages
6. **Push your branch** to GitHub
7. **Create a Pull Request** following the PR template

## Code Quality

### Code Formatting and Linting

We use [Ruff](https://github.com/astral-sh/ruff) for both linting and formatting. Ruff is fast and combines the functionality of multiple tools (black, flake8, isort, etc.).

**Before committing, run:**

```bash
# Check for linting issues
make lint
# Or: ruff check .

# Auto-format code
make format
# Or: ruff format .
```

### Type Checking

We use mypy for optional type checking (currently permissive):

```bash
mypy the_flip
```

### Pre-commit Hooks

If you installed pre-commit hooks (`pre-commit install`), these checks run automatically before each commit. If checks fail, the commit is blocked until you fix the issues.

To manually run all pre-commit checks:
```bash
pre-commit run --all-files
```

### Configuration

Tool configurations are in `pyproject.toml`:
- Ruff linting rules
- Ruff formatting options
- Mypy type checking settings
- Coverage reporting settings

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run tests with fresh database
make test-clean

# Run tests in parallel (faster)
make test-fast

# Run tests with verbose output
make test-verbose
```

### Test Coverage

```bash
# Generate coverage report
make coverage

# View HTML coverage report
# Opens in browser: htmlcov/index.html
```

### Writing Tests

- Follow Django's testing conventions
- Tests live in `tests.py` or `tests/` directories within each app
- See [docs/Testing.md](docs/Testing.md) for detailed testing guidelines
- Aim for good coverage of critical paths, especially:
  - Authentication and permissions
  - Form validation
  - Business logic in models
  - View access controls

## Pull Request Process

1. **Ensure all tests pass** locally before pushing
2. **Update documentation** if you've changed APIs or added features
3. **Push your branch** to GitHub
4. **Create a Pull Request** against the `main` branch
5. **Fill out the PR template** with:
   - Clear description of what changed and why
   - Testing steps performed
   - Any related issues
6. **Address review feedback** by pushing new commits to your branch
7. **Wait for approval** - maintainers will review and may request changes
8. **Merge** - Once approved, your PR will be merged

### PR Environment Testing

When you create a PR, Railway automatically deploys your changes to a temporary PR environment. You'll get a unique URL (e.g., `pr-123.up.railway.app`) to click-test your changes in a live environment before merging to production.

**Note:** Merging to `main` automatically deploys to production at https://the-flip-production.up.railway.app/

## Branch Naming Convention

Branch names should follow this pattern: `<type>/<author>/<brief-description>`

### Types

- `feat` - New features or enhancements
- `fix` - Bug fixes
- `docs` - Documentation changes
- `chore` - Maintenance tasks (dependencies, tooling, config)
- `test` - Test additions or modifications
- `refactor` - Code refactoring without functional changes

### Author

Your username or identifier (e.g., `moses`, `claude`, `yourname`)

### Examples

- `feat/claude/add-contributing-guide`
- `fix/moses/video-upload-timeout`
- `docs/claude/architecture-overview`
- `chore/moses/update-dependencies`
- `test/claude/add-catalog-tests`

## Commit Messages

Write clear, descriptive commit messages:

**Good:**
```
Add pre-commit hooks for code quality checks

- Configure ruff for linting and formatting
- Add mypy for type checking
- Update CONTRIBUTING.md with setup instructions
```

**Avoid:**
```
fixed stuff
wip
updates
```

## Questions or Issues?

- Review the [documentation](docs/README.md) first
- Check existing [GitHub Issues](https://github.com/deanmoses/the_flip/issues)
- Create a new issue if you're stuck or found a bug
- For security issues, see [SECURITY.md](SECURITY.md) (if applicable)

## Code of Conduct

Be respectful, collaborative, and constructive. This is a community project for a pinball museum - keep it fun!

---

Thank you for contributing to The Flip! 🎮
