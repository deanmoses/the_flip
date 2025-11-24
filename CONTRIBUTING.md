# Contributing

This guide covers how to contribute to the project and submit a PR.


## Getting Started

 - Get your environment configured in [README.md](README.md)
 - Understand developing conventions in [docs/README.md](docs/README.md)

## Workflow

-  **Create a branch** with a descriptive name (e.g., `fix/login-bug`, `docs/api-guide`)
- **Make your changes & tests**
```bash
make quality     # Format, lint, check Python types
make test        # Run suite
```
- **Commit changes**
- **Push branch to GitHub**
- **Create a Pull Request** against `main`
- **Wait for CI checks**. GitHub Actions will automatically run tests, linting, type checking, etc
- **Test in hosted env**. A temporary environment is automatically created for testing, see [docs/Deployment.md](docs/Deployment.md)
- **Merge when ready**. You can self-merge PR once CI passes
