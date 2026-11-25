# Progress

Day 31 - Completed:
- Problem statement, user roles, MVP, user stories and acceptance criteria
- Architecture diagram and technology decisions
- Individual team roles
- GitHub repository, README and .gitignore

Day 32 - Completed:
- Database schema (items, audit_log) with SQLAlchemy
- CRUD endpoints under /items with role checks and audit log
- Deterministic scoring: probability x impact with priority bands
- AI suggestion endpoint (/suggest), marked as suggestions
- Similar-risk search using TF-IDF and FAISS
- Sample register with 30 records
- Endpoints tested in Swagger UI

Day 33 - Completed:
- React (Vite) dashboard: summary strip, risk matrix, filters, register table
- Record form with AI draft and role-based review workflow
- Backend middleware: request logging and error handling
- UI test checklist in docs/ui_testing.md
- Code review fixes: required role header, enforced review life cycle, protected review notes
- RAG: AI draft uses the 3 most similar past risks (TF-IDF + FAISS)
- Tested with PostgreSQL locally (pgAdmin)
- AI import: extract risks and issues from emails or meeting notes as drafts for review
- Banking scope: clearer problem statement, 48 banking programme risks, banking rules in AI prompts
- Bank policy upload: AI mitigations follow uploaded policy PDFs and cite the page

Day 34 - Completed:
- AI moved from Groq to Azure OpenAI
- Backend containerised with Docker and tested locally
- Backend tests with pytest (scoring, roles, review workflow, audit log, scope check, citation guard)
- CI/CD with GitHub Actions: lint, tests, frontend build, Docker smoke test, image published to GHCR, Azure deploy steps ready
- Dependabot for weekly dependency updates; Python packages pinned
- Hardening: container runs as non-root, AI errors no longer expose internal details
- Structured AI output: cause, potential impact, warning indicators, preventive, corrective and contingency actions
- Citation guard: unsupported policy, page and regulation citations removed
- Scope check: out-of-scope text gets a fallback message instead of a draft
- AI evaluation: 15 cases, human review 14/15 accepted, fallback 3/3, adversarial 2/2 (docs/evaluation.md)
- Locust load test: 20 users for 1 minute, p95 29 ms, 0.18% errors (docs/testing.md)
- App screenshots for documentation and slides (docs/screenshots)
- One container: FastAPI serves the React app at / and the API under /api (56 tests)
- Deployed on Azure: App Service (one container), Azure PostgreSQL, Azure OpenAI
- CD deploys automatically to the Web App on every push to master
- Live screenshot of the deployed app (docs/screenshots/06_live_azure.png)