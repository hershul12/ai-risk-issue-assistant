from fastapi import FastAPI
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
    return analyze_risk(data.description)


@app.post("/similar")
def similar(data: RiskInput):
    return search_similar(data.description)