Backend — Quick Start
Setup
cd backend
docker compose up -d --build

# stop:

docker compose down

Tests (SQLite settings) — run from backend/
unset DJANGO_SETTINGS_MODULE
export PYTHONPATH="$PWD"
poetry run python -c "import importlib; importlib.import_module('config.settings.test_sqlite'); print('OK')"
poetry run pytest -m "not pg_only" -q

Coverage
poetry run pytest -m "not pg_only" --cov=apps --cov-report=term-missing

# HTML report:

# poetry run pytest -m "not pg_only" --cov=apps --cov-report=html (open htmlcov/index.html)

Lint / Format
poetry run isort .
poetry run black .
poetry run flake8 .
poetry run pre-commit install
poetry run pre-commit run --all-files

Makefile
make up # docker compose up -d --build
make migrate # manage.py migrate
make test # pytest -m "not pg_only"
make lint # isort + black + flake8

URLs

Admin: http://localhost:8000/admin/

API docs: http://localhost:8000/api/schema/swagger-ui/
