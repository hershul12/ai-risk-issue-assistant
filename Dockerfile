# Backend image for RiskPilot (build from the project root)
FROM python:3.12-slim

WORKDIR /app

# Install packages first so Docker can reuse this step when only code changes
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the code and the sample data
COPY backend/ backend/
COPY data/ data/

WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
