# RiskPilot: AI-Powered Project Risk & Issue Triage and Mitigation

A risk and issue register for financial services programmes. It scores records with fixed rules, uses AI to draft clearer descriptions and mitigation plans for human review, and controls status changes by role with a full audit log.

**Domain:** Financial Risk Management
**Users:** Project Manager, Risk/Issue Owner, Programme Lead
**Tech Stack:** React (Vite), FastAPI, SQLite, Groq API (GPT-OSS), TF-IDF + FAISS, Azure

## Features
- Register with standard fields, owner, due date and status
- Score = Probability x Impact (Low 1-5, Medium 6-12, High 13-19, Critical 20-25)
- AI-drafted description, category and mitigation, shown as suggestions only
- Review workflow: Open -> In Progress -> Pending Review -> Closed
- Role-based permissions and audit log
- Dashboard with filters and a 5 x 5 risk matrix

## Setup
Create `.env` in the project root (see `.env.example`):
```
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

## Run the Backend
```
venv\Scripts\activate
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

## Run the Frontend
```
cd frontend
npm install
npm run dev
```
App: http://localhost:5173

## Project Plan
- [x] Day 31: Define and design
- [x] Day 32: Backend and AI
- [x] Day 33: Frontend and integration
- [ ] Day 34: Deployment and testing
- [ ] Day 35: Demo and documentation

See `docs/` for the problem statement, requirements and architecture.