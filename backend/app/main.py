from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.llm_service import analyze_risk
from app.services.vector_service import search_similar

app = FastAPI(title="RiskPilot: Financial Risk & Issue Triage and Mitigation Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RiskInput(BaseModel):
    description: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(data: RiskInput):
    try:
        similar_risks = search_similar(data.description)
        result = analyze_risk(data.description, similar_risks)
        result["similar_risks"] = similar_risks
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@app.post("/similar")
def similar(data: RiskInput):
    try:
        return search_similar(data.description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")