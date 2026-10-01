FROM python:3.12-slim

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy configuration files
COPY pyproject.toml poetry.lock* /app/

# Synchronize lockfile and install dependencies directly to system site-packages
RUN poetry config virtualenvs.create false \
    && poetry lock \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application source code
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
