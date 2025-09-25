Setup


1. cd backend
2. cp .env.example .env
3. python -m venv .venv && source .venv/bin/activate
4. pip install -r requirements.txt
5. pre-commit install
6. docker compose up -d --build


Makefile


make up
make migrate
make test
make lint


URLs


http://localhost:8000/health/
http://localhost:8000/admin/
http://localhost:8000/api/docs/