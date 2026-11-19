# RiskPilot: AI-Powered Project Risk & Issue Triage and Mitigation

A project risk and issue assistant that captures records, standardises
descriptions, suggests categorisation and drafts mitigation and follow-up
actions for owners to review.

## Domain
Financial Risk Management

## Target Users
Project manager, risk/issue owner, programme lead

## MVP
Create/read/update risk and issue register, deterministic scoring,
AI-drafted mitigation suggestions, dashboard with filters, audit log.

## Tech Stack
React, FastAPI, SQLite, Groq API (GPT-OSS), Azure

## Project Plan
- [x] Day 31: Define and design
- [ ] Day 32: Backend and AI
- [ ] Day 33: Frontend and integration
- [ ] Day 34: Deployment and testing
- [ ] Day 35: Demo and documentation

## Run the Backend
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs to test the API.