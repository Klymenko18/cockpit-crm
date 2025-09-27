FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 build-essential gcc libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Встановлюємо Poetry і працюємо БЕЗ virtualenv (щоб "pytest", "gunicorn" були в PATH контейнера)
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir "poetry>=1.8" \
 && poetry config virtualenvs.create false

# Спочатку тільки маніфести — кешується інсталяція залежностей
COPY pyproject.toml /app/pyproject.toml
# (опційно, якщо згенеруєш лок: COPY poetry.lock /app/poetry.lock)

# Якщо lock-файла нема — згенерувати його всередині образу й встановити залежності
RUN poetry lock --no-interaction || true \
 && poetry install --no-interaction --no-ansi --only main

# Тепер — увесь код
COPY . /app

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000