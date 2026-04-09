FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY scripts /app/scripts
COPY src /app/src

RUN pip install --upgrade pip && pip install .

RUN mkdir -p /app/.artifacts /app/data

EXPOSE 8000

CMD ["uvicorn", "fars_kg.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
