FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Byte-compile for faster startup
ENV UV_COMPILE_BYTECODE=1
# Install into the system Python (no extra .venv inside container)
ENV UV_PROJECT_ENVIRONMENT=/usr/local

# Install dependencies first (layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project --no-dev --frozen

# Copy application code
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
