# Testing

RiskPilot is tested in three ways:

| Type | Tool | What it covers | Calls Azure OpenAI? |
|------|------|----------------|---------------------|
| Unit and API tests | Pytest | Scoring, roles, review workflow, audit log, citation guard, scope check, serving the React app and the /api routes | No (AI is mocked) |
| Load test | Locust | Dashboard endpoints under 20 concurrent users | No (AI endpoints excluded) |
| AI evaluation | `backend/eval/run_eval.py` | Quality of "Draft with AI" on 15 cases, with human review | Yes |

## Unit and API tests (Pytest)

Run from the project root:

```
cd backend
pip install -r requirements-dev.txt
pytest -q
```

Result on 2026-11-25: **56 passed, 0 failed** (1.5 s).

| Test file | Tests | Covers |
|-----------|-------|--------|
| `tests/test_scoring.py` | 10 | Score = probability x impact, priority bands, overdue rule |
| `tests/test_api.py` | 11 | Health, list and create records, role checks, review workflow (no closing without review), audit log, safe AI error messages, structured AI draft, citation removal |
| `tests/test_citations.py` | 12 | Citation guard: keeps valid policy citations; removes invented policies, pages not retrieved, pages that do not cover the action, and placeholder or invented regulation numbers |
| `tests/test_scope.py` | 13 | Out-of-scope fallback (nothing retrieved or drafted), in-scope behaviour unchanged, invalid categories dropped, Import from text unaffected |
| `tests/test_frontend.py` | 10 | Every API route also works under `/api` (same responses, role checks, listed in the API docs); the built React app is served at `/` with its assets and a page fallback; unknown `/api` paths stay JSON 404s; no files served from outside the build; no frontend when there is no build |

The Azure OpenAI client is replaced with a fake in every test, so the tests are free, fast and repeatable. They also run in CI on every pull request.

## Load test (Locust)

### How to run

With the backend running at http://127.0.0.1:8000, from the project root:

```
pip install -r backend/requirements-dev.txt
venv\Scripts\locust -f backend/loadtest/locustfile.py --host http://127.0.0.1:8000 --headless -u 20 -r 5 -t 1m --csv backend/loadtest/results/riskpilot --only-summary
```

To watch it live in a browser instead, leave out `--headless ... --only-summary` and open http://localhost:8089.

CSV results are written to `backend/loadtest/results/` (git-ignored). The load test is not part of CI.

### What it simulates

Each virtual user is a person using the dashboard (`backend/loadtest/locustfile.py`):

- On start: loads the register (`GET /items`) and the summary (`GET /dashboard/summary`).
- Then, with 2 to 6 seconds of reading time between actions:
  - opens a record: `GET /items/{id}` and `GET /items/{id}/audit` (weight 4)
  - refreshes the register and summary (weight 3)
  - reloads the summary (weight 2)
  - `GET /health`, as a monitoring probe would (weight 1)

**AI endpoints are excluded.** `/suggest` and `/extract` are not called because every request makes a paid call to Azure OpenAI, an external service. Their quality and response time are measured separately in the AI evaluation (`docs/evaluation.md`: about 5 s on average per draft).

### Settings used

Measured locally on 2026-11-24, **before** the app was deployed to Azure.

| Setting | Value |
|---------|-------|
| Date | 2026-11-24 |
| Users | 20 |
| Spawn rate | 5 users per second |
| Duration | 1 minute |
| Wait time | 2 to 6 seconds between actions |
| Target | Local backend, `uvicorn --reload` (single worker), SQLite, 34 records |
| Machine | Same Windows Server machine for Locust and the backend |

### Results

| Metric | Result |
|--------|--------|
| Total requests | 542 |
| Requests per second | 9.3 |
| Median response time | 7 ms |
| p95 response time | 29 ms |
| Average response time | 10 ms |
| Errors | 1 (0.18%) |

| Endpoint | Requests | Failures | Median (ms) | p95 (ms) |
|----------|----------|----------|-------------|----------|
| `GET /dashboard/summary` | 154 | 0 | 7 | 30 |
| `GET /health` | 26 | 0 | 5 | 7 |
| `GET /items` | 111 | 0 | 9 | 37 |
| `GET /items/{id}` | 126 | 1 | 7 | 17 |
| `GET /items/{id}/audit` | 125 | 0 | 6 | 11 |

Figures are from the saved CSV (`riskpilot_stats.csv`). The console summary showed 545 requests because it also counts a few requests that finished while Locust was shutting down.

### Notes

- **The one error** was a `ConnectionResetError` (Windows error 10054) on `GET /items/{id}`: the connection was closed at the network level before the request reached the app. The backend logged 544 requests in that minute, all with status 200, and no application errors. It is counted as an error above.
- **Requests per second reflects realistic use, not maximum capacity.** With 2 to 6 seconds of thinking time, 20 users generate about 9 requests per second. All response times stayed well under 100 ms, so this load is comfortably handled.
- **This was a local development setup, measured before deployment** (auto-reload server, SQLite, client and server on one machine). The app now runs on Azure App Service with Azure PostgreSQL; results there will differ and have not been re-measured yet.

## AI evaluation

The quality of the AI features is tested separately, because it needs the real Azure OpenAI service. See **[docs/evaluation.md](evaluation.md)** for the 15 test cases (in scope, out of scope and adversarial), the automatic checks, the before/after comparison, and the human review: 14 of 15 cases accepted.
