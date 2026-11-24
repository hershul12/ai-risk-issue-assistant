# RiskPilot: AI-Powered Project Risk & Issue Triage and Mitigation

A governed risk and issue register for banking technology programmes. It scores records with a fixed formula, uses Azure OpenAI to extract risks from emails and draft structured mitigation plans grounded in past banking risks and the bank's own policies, and requires review and approval before a record is closed.

**Domain:** Financial Risk Management (banking technology programmes)
**Users:** Project Manager, Risk/Issue Owner, Programme Lead
**Tech Stack:** React (Vite), FastAPI, PostgreSQL, Azure OpenAI, TF-IDF + FAISS, Docker, Azure

## Features
- Register with standard fields, owner, due date and status
- Score = Probability x Impact (Low 1-5, Medium 6-12, High 13-19, Critical 20-25)
- Draft with AI: structured risk assessment with cause, potential impact, warning indicators, and preventive, corrective and contingency actions
- Import from text: AI finds risks and issues in emails or meeting notes
- RAG: AI uses similar past banking risks and uploaded bank policy PDFs as context, citing the policy and page
- Citation guard: unsupported policy, page and regulation citations are removed before the user sees them
- Scope check: out-of-scope text gets a clear fallback message instead of an AI draft
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

## Run the Tests
```
cd backend
pip install -r requirements-dev.txt
pytest
```
46 tests run with the AI mocked, so Azure is never called in tests.

## AI Evaluation
The AI was evaluated on 15 test cases against Azure OpenAI, with an AI-assisted first pass and a final human review.

| Check | Result |
|-------|--------|
| Reviewer accepted (all cases) | 14/15 (93%) |
| In-scope drafts accepted | 9/10 (90%) |
| Out-of-scope cases with correct fallback | 3/3 (100%) |
| Adversarial cases handled | 2/2 (100%) |
| Unsupported citations in final drafts | 0 |

Full results, before/after comparison and how to re-run: `docs/evaluation.md`. The sample policy used is `data/sample_policies/Vendor_Management_Policy.pdf` (synthetic, not a real bank policy).

## CI/CD (GitHub Actions)
- **CI** (`.github/workflows/ci.yml`, on pull requests): backend lint + pytest, frontend lint + build, Docker build with a `/health` smoke test.
- **CD** (`.github/workflows/cd.yml`, on push to `master` or a `v*` tag): runs CI, then pushes the backend image to `ghcr.io/<owner>/<repo>/riskpilot-api` (tags `latest`, `sha-<commit>`, and the version for tags).
- **Backend deploy** (optional): add the repo variable `AZURE_WEBAPP_NAME` and secret `AZURE_WEBAPP_PUBLISH_PROFILE` to deploy the image to an Azure Web App. Skipped until they are set. Set these app settings on the Web App: `WEBSITES_PORT=8000`, `AZURE_OPENAI_*`, `DATABASE_URL` (add `?sslmode=require` for Azure PostgreSQL) and `ALLOWED_ORIGINS` (the frontend URL). Keep it at one instance (see `docs/architecture.md`).
- **Frontend deploy** (optional): set the repo variable `VITE_API_URL` (the backend URL), the variable `DEPLOY_FRONTEND_TO_AZURE=true` and the secret `AZURE_STATIC_WEB_APPS_API_TOKEN` to deploy to Azure Static Web Apps. Skipped until they are set.
- **Dependabot** (`.github/dependabot.yml`): weekly update PRs for GitHub Actions, pip, npm and the Docker base image.

## Project Plan
- [x] Day 31: Define and design
- [x] Day 32: Backend and AI
- [x] Day 33: Frontend and integration
- [ ] Day 34: Deployment and testing
- [ ] Day 35: Demo and documentation

See `docs/` for the problem statement, requirements, architecture and AI evaluation.