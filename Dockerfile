# Backend image for RiskPilot (build from the project root)
FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install packages first so Docker can reuse this step when only code changes
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Run as a non-root user. It owns data/ so the SQLite fallback can still write there.
RUN useradd --create-home --uid 1000 appuser

# Copy the code and the sample data
COPY backend/ backend/
COPY --chown=appuser:appuser data/ data/

USER appuser
WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
