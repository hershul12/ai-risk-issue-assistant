# RiskPilot: AI-Powered Financial Risk & Issue Triage and Mitigation Assistant

An AI assistant for banks and financial institutions that classifies
financial risks and issues, rates their severity and probability, and
suggests mitigation actions using similar past incidents.

## Domain
Banking & Financial Services (Financial Risk Management)

## Tech Stack
React, FastAPI, Groq API (GPT-OSS), FAISS, scikit-learn, Azure

## Project Plan
- [x] Day 31: Project setup and architecture
- [x] Day 32: Backend and AI integration
- [ ] Day 33: Frontend and middleware
- [ ] Day 34: Deployment and testing
- [ ] Day 35: Demo and documentation

## Run the Backend
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs to test the API.