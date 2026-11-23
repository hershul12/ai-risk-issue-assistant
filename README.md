# RiskPilot: AI-Powered Project Risk & Issue Triage and Mitigation

A governed risk and issue register for banking technology programmes. It scores records with a fixed formula, uses Azure OpenAI to extract risks from emails and draft descriptions and mitigation plans grounded in past banking risks and the bank's own policies, and requires review and approval before a record is closed.

**Domain:** Financial Risk Management (banking technology programmes)
**Users:** Project Manager, Risk/Issue Owner, Programme Lead
**Tech Stack:** React (Vite), FastAPI, PostgreSQL, Azure OpenAI, TF-IDF + FAISS, Docker, Azure

## Features
- Register with standard fields, owner, due date and status
- Score = Probability x Impact (Low 1-5, Medium 6-12, High 13-19, Critical 20-25)
- Draft with AI: clearer description, category, mitigation and follow-up actions
- Import from text: AI finds risks and issues in emails or meeting notes
- RAG: AI uses similar past banking risks and uploaded bank policy PDFs as context
- Review workflow: Open -> In Progress -> Pending Review -> Closed
- Role-based permissions and full audit log
- Dashboard with filters and a 5 x 5 risk matrix

## Setup
Create `.env` in the project root (see `.env.example`):
```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
AZURE_OPENAI_API_VERSION=2024-10-21
```
To use PostgreSQL, set `DATABASE_URL` before starting the backend. Without it, a local SQLite file is used.

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

## Run with Docker (backend)
```
docker build -t riskpilot-api .
docker run -d --name riskpilot --env-file .env -p 8000:8000 riskpilot-api
```

## Project Plan
- [x] Day 31: Define and design
- [x] Day 32: Backend and AI
- [x] Day 33: Frontend and integration
- [ ] Day 34: Deployment and testing
- [ ] Day 35: Demo and documentation

See `docs/` for the problem statement, requirements and architecture.