# ==============================================================================
# INGRES AI Production Multi-Stage Dockerfile
# Builds the Vite React Frontend and runs the FastAPI Backend with Uvicorn
# ==============================================================================

# --- Stage 1: Build Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Backend ---
FROM python:3.12-slim AS runner
WORKDIR /app

# Install system dependencies for PostgreSQL and healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY backend /app/backend

# Copy built frontend static bundle
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Set Python environment path
ENV PYTHONPATH=/app/backend
ENV PORT=8000
EXPOSE 8000

# Health check to ensure zero-downtime deployments
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Start Uvicorn with production worker configuration
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}
