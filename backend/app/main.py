from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.services.llm_service import analyze_risk
from app.services.vector_service import search_similar

app = FastAPI(title="RiskPilot: Financial Risk & Issue Triage and Mitigation Assistant")


class RiskInput(BaseModel):
    description: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(data: RiskInput):
    try:
        return analyze_risk(data.description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@app.post("/similar")
def similar(data: RiskInput):
    try:
        return search_similar(data.description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")