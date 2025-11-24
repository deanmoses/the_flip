.PHONY: help
help:
	@echo "Django project Makefile commands:"
	@echo ""
	@echo "Development:"
	@echo "  make runserver      - Start development server"
	@echo "  make runq           - Start Django Q cluster worker"
	@echo "  make shell          - Start Django shell"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run tests with database reuse"
	@echo "  make test-clean     - Run tests with fresh database"
	@echo "  make test-verbose   - Run tests with verbose output"
	@echo "  make test-fast      - Run tests in parallel"
	@echo "  make coverage       - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Check code and templates"
	@echo "  make format         - Auto-format code and templates"
	@echo "  make typecheck      - Run mypy type checker"
	@echo "  make quality        - Format code and run all quality checks"
	@echo "  make precommit      - Run pre-commit hooks on all files"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrations     - Create new migrations"
	@echo "  make superuser      - Create superuser"
	@echo "  make reset-db       - Reset database and migrations"
	@echo ""
	@echo "Data:"
	@echo "  make import-data    - Import legacy data"
	@echo ""

.PHONY: test
test:
	DJANGO_SETTINGS_MODULE=the_flip.settings.test .venv/bin/python manage.py test --keepdb

.PHONY: test-clean
test-clean:
	DJANGO_SETTINGS_MODULE=the_flip.settings.test .venv/bin/python manage.py test

.PHONY: test-ci
test-ci:
	DJANGO_SETTINGS_MODULE=the_flip.settings.test python manage.py test --no-input --failfast

.PHONY: test-verbose
test-verbose:
	DJANGO_SETTINGS_MODULE=the_flip.settings.test .venv/bin/python manage.py test --keepdb --verbosity=2

.PHONY: test-fast
test-fast:
	DJANGO_SETTINGS_MODULE=the_flip.settings.test .venv/bin/python manage.py test --keepdb --parallel

.PHONY: runserver
runserver:
	.venv/bin/python manage.py runserver

.PHONY: migrate
migrate:
	.venv/bin/python manage.py migrate

.PHONY: migrations
migrations:
	.venv/bin/python manage.py makemigrations

.PHONY: shell
shell:
	.venv/bin/python manage.py shell

.PHONY: superuser
superuser:
	.venv/bin/python manage.py createsuperuser

.PHONY: runq
runq:
	.venv/bin/python manage.py qcluster

.PHONY: reset-db
reset-db:
	./reset_migrations.sh

.PHONY: import-data
import-data:
	.venv/bin/python manage.py import_legacy_data

.PHONY: lint
lint:
	.venv/bin/ruff check .
	.venv/bin/djlint templates/ --check

.PHONY: format
format:
	.venv/bin/ruff format .
	.venv/bin/djlint templates/ --reformat --quiet

.PHONY: typecheck
typecheck:
	.venv/bin/mypy the_flip

.PHONY: quality
quality: format lint typecheck
	@echo "All quality checks passed!"

.PHONY: precommit
precommit:
	@echo "Running pre-commit checks..."
	.venv/bin/pre-commit run --all-files

.PHONY: coverage
coverage:
	DJANGO_SETTINGS_MODULE=the_flip.settings.test .venv/bin/coverage run manage.py test
	.venv/bin/coverage report
	.venv/bin/coverage html
	@echo "Coverage report generated in htmlcov/index.html"
