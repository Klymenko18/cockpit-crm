FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 build-essential gcc libpq-dev \
  && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir "poetry>=1.8" \
 && poetry config virtualenvs.create false

COPY pyproject.toml /app/pyproject.toml
RUN poetry lock --no-interaction || true \
 && poetry install --no-interaction --no-ansi --only main

COPY . /app

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000