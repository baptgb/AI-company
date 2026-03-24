FROM node:20-slim AS frontend-builder

WORKDIR /build/dashboard
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build


FROM python:3.11-slim AS backend

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e ".[full]"

COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY docker/ ./docker/
COPY plugin/ ./plugin/
COPY hooks/ ./hooks/

COPY --from=frontend-builder /build/dashboard/dist ./dashboard/dist

EXPOSE 8000

CMD ["uvicorn", "aiteam.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
