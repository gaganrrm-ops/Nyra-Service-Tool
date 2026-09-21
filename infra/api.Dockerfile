FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml /app/apps/api/pyproject.toml
RUN pip install --upgrade pip && pip install -e /app/apps/api || pip install -e "/app/apps/api[all]"

COPY apps/api /app/apps/api
COPY db /app/db
WORKDIR /app/apps/api
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --retries=10 CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "nyra_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
