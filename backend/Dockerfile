# ============================================================
# Traveo Backend — Dockerfile (Multi-Stage, Production-Ready)
# ============================================================

# ── Stage 1: Builder ─────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (Docker layer caching)
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir --prefix=/install .

# ── Stage 2: Production ─────────────────────────────────────
FROM python:3.11-slim AS production

# Security: non-root user
RUN groupadd -r traveo && useradd -r -g traveo -d /app -s /sbin/nologin traveo

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Set ownership
RUN chown -R traveo:traveo /app

# Switch to non-root user
USER traveo

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop"]
