FROM python:3.13-slim

WORKDIR /app
COPY . .

RUN pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.in-project true
RUN poetry run pip install -U setuptools==57.0.0
RUN poetry self add poetry-plugin-export
RUN poetry export --without-hashes -f requirements.txt > requirements.txt
RUN pip install -r requirements.txt

RUN poetry install --without dev
