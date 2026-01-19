# syntax=docker/dockerfile:1.7

################
# DEPENDENCIES #
################
FROM python:3.12-slim AS deps

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Build-time system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxmlsec1 \
    libxmlsec1-dev \
    build-essential \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependency-related files
COPY README.rst setup.py ./
COPY bluebottle/__init__.py bluebottle/__init__.py

# Pin pip for legacy Celery 4.3.1
RUN pip install --upgrade "pip<24.1" setuptools wheel \
    && pip install -e .[env]

###############
# RUNTIME     #
###############
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Runtime-only dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    postgis \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtualenv from deps stage
COPY --from=deps /opt/venv /opt/venv

# Copy application source
COPY . .

ENV PATH="/opt/venv/bin:$PATH"

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Optional: dev bash history
ENV HISTFILE="/opt/data/.bash_history"

