# RiskPilot in one container: FastAPI serves the API (/api) and the built React app (/).
# Build from the project root: docker build -t riskpilot .

# ---- Stage 1: build the React app ----
FROM node:22-slim AS frontend
WORKDIR /frontend
# Install packages first so Docker can reuse this step when only code changes
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# No VITE_API_URL: the app calls /api on the same origin
RUN npm run build

# ---- Stage 2: the backend image, which also serves the built frontend ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install packages first so Docker can reuse this step when only code changes
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Run as a non-root user. It owns data/ so the SQLite fallback can still write there.
RUN useradd --create-home --uid 1000 appuser

# Copy the code, the sample data and the built frontend (read-only for appuser)
COPY backend/ backend/
COPY --chown=appuser:appuser data/ data/
COPY --from=frontend /frontend/dist frontend/dist

USER appuser
WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
