# Progress

Day 31 - Completed:
- Problem statement, user roles, MVP, user stories and acceptance criteria
- Architecture diagram and technology decisions
- Individual team roles
- GitHub repository, README and .gitignore

Day 32 - Completed:
- SQLite schema (items, audit_log) with SQLAlchemy
- CRUD endpoints under /items with role checks and audit log
- Deterministic scoring: probability x impact with priority bands
- AI suggestion endpoint (/suggest) using Groq, marked as suggestions
- Sample register with 30 records
- Tested GET /items, GET /dashboard/summary and POST /items

Day 33 - Completed:
- React (Vite) dashboard: summary strip, risk matrix, filters, register table
- Record form with AI draft and role-based review workflow
- Backend middleware: request logging and error handling
- UI test checklist in docs/ui_testing.md
- Code review fixes: required role header, enforced review life cycle, protected review notes
- RAG: AI draft uses the 3 most similar past risks (TF-IDF + FAISS)
- Tested with PostgreSQL locally (pgAdmin)
- README and docs updated