FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    sqlite3 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install poetry

RUN poetry config virtualenvs.in-project true

# 依存関係ファイルのみを先にコピー（キャッシュ効率化）
COPY pyproject.toml poetry.lock* ./

RUN poetry install --without dev --no-root

COPY . .

RUN poetry install --without dev

RUN mkdir -p /app/db
