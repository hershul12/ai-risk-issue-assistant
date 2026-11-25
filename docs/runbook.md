# Runbook

How to configure, run, deploy, monitor and fix RiskPilot.

## 1. Overview

| Part | What it is |
|------|------------|
| App | One Docker container. FastAPI serves the React app at `/` and the API under `/api` (also at the root path for tools and tests). Port 8000. |
| Hosting | Azure App Service (Web App for Containers), one instance |
| Database | Azure Database for PostgreSQL (tables `items`, `audit_log`, `policy_documents`, `policy_chunks`) |
| AI | Azure OpenAI (chat deployment, for example `gpt-4o-mini`) |
| Retrieval | TF-IDF + FAISS, in memory inside the container |
| CI/CD | GitHub Actions: CI on pull requests; CD on push to `master` builds the image, pushes it to GHCR and deploys it to the Web App |

Without `DATABASE_URL` the app uses a local SQLite file (`data/risk_register.db`).

## 2. Configuration

Never put real values in this file, in Git or in screenshots. Locally they go in `.env`
(copy `.env.example`); on Azure they go in **Web App > Settings > Environment variables
(App settings)**.

| Setting | Where | Required | Description |
|---------|-------|----------|-------------|
| `WEBSITES_PORT` | Azure only | Yes | `8000`. Tells App Service which port the container listens on. |
| `AZURE_OPENAI_ENDPOINT` | `.env` and Azure | Yes for AI | Resource endpoint, for example `https://<resource>.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | `.env` and Azure | Yes for AI | Key from the Azure OpenAI resource (Keys and Endpoint) |
| `AZURE_OPENAI_DEPLOYMENT` | `.env` and Azure | Yes for AI | The **deployment name** you created in Azure AI Foundry, not the model family name. Default `gpt-4o-mini`. |
| `AZURE_OPENAI_API_VERSION` | `.env` and Azure | No | Default `2024-10-21` |
| `DATABASE_URL` | Azure (optional locally) | Yes on Azure | `postgresql://<user>:<password>@<server>.postgres.database.azure.com:5432/<database>?sslmode=require` |
| `ALLOWED_ORIGINS` | Optional | No | Comma-separated website URLs allowed to call the API from another origin. Not needed when the website and API share one URL. |

**`DATABASE_URL` notes**
- Azure PostgreSQL requires SSL: always end the address with `?sslmode=require`.
- Special characters in the password must be **URL-encoded**, otherwise the address is
  read wrongly and the app cannot start. Common ones: `@` -> `%40`, `#` -> `%23`,
  `/` -> `%2F`, `:` -> `%3A`, `%` -> `%25`, `?` -> `%3F`. Example: password `Ab@12` is written
  `Ab%4012`. Encode it in Python with
  `python -c "from urllib.parse import quote; print(quote('your-password', safe=''))"`.

**GitHub settings used by CD** (repo **Settings > Secrets and variables > Actions**)

| Name | Type | Value |
|------|------|-------|
| `AZURE_WEBAPP_NAME` | Variable | Name of the Web App. If empty, the deploy job is skipped. |
| `AZURE_WEBAPP_PUBLISH_PROFILE` | Secret | Contents of the publish profile downloaded from the Web App (**Overview > Download publish profile**) |
| `GITHUB_TOKEN` | Built in | Used to push the image to GHCR; nothing to set |

## 3. Run locally

**Docker (whole app, one URL)**, from the project root:
```
docker build -t riskpilot .
docker run -d --name riskpilot --env-file .env -p 8000:8000 riskpilot
```
Open http://127.0.0.1:8000 (website), http://127.0.0.1:8000/api/health (health) and
http://127.0.0.1:8000/docs (API docs). Stop with `docker stop riskpilot`, remove with
`docker rm riskpilot`.

**Development mode (hot reload)**, two terminals:
```
# Terminal 1: backend on http://127.0.0.1:8000
venv\Scripts\activate
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 2: frontend on http://localhost:5173
cd frontend
npm install
npm run dev
```
The website calls `/api` on its own origin and the Vite dev server forwards `/api` to the
backend, so no API URL is needed.

## 4. Deploy

1. Merge or push to `master`.
2. **CD** (`.github/workflows/cd.yml`) runs:
   - **CI**: backend lint + pytest, frontend lint + build, Docker build + smoke test.
   - **Publish image**: pushes `ghcr.io/<owner>/<repo>/riskpilot-api` with tags `latest` and
     `sha-<full commit id>`.
   - **Deploy to Azure App Service**: points the Web App at the new `sha-<commit>` image.
3. **Check the run:** GitHub repo > **Actions** > **CD** > the latest run. All jobs should be
   green (the Static Web Apps job is always skipped; that is expected). From the terminal:
   `gh run list --workflow cd.yml --limit 5` and `gh run watch`.
4. **Check the app:** open `<app URL>/api/health` (expect `{"status":"ok"}`), then the website.
   The first request after a deploy can take 30-60 seconds while the container starts.

**Roll back** to an earlier version:
- **Option A (Azure portal):** Web App > **Deployment Center** > set the image tag to the
  previous good `sha-<commit>` (find it under the repo's **Packages** or in the earlier CD run)
  > **Save**, then **Restart**.
- **Option B (GitHub):** `git revert <bad commit>` and push to `master`; CD deploys the
  reverted code as a new image.
- **Option C (Azure CLI):**
  ```
  az webapp config container set --name <app> --resource-group <rg> \
    --container-image-name ghcr.io/<owner>/<repo>/riskpilot-api:sha-<good commit>
  az webapp restart --name <app> --resource-group <rg>
  ```
Database changes are not rolled back by redeploying an image.

## 5. Monitor

- **Health:** `GET /api/health` returns `{"status": "ok"}` when the app is running.
- **Log Stream:** Web App > **Monitoring > Log stream** shows container start-up messages
  and the app's logs live. **Diagnose and solve problems** helps with start-up failures.
- **Request logs:** the middleware (`backend/app/middleware.py`) writes one line per request:
  ```
  2026-11-25 10:15:02 INFO GET /api/items status=200 time=12ms role=Project Manager
  ```
  Unhandled errors are logged with the full traceback as `Unhandled error on <method> <path>`
  and the user gets a safe 500 message. AI failures are logged as `AI <action> failed` and
  the user gets a 502.

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| 503 / "Application Error", container keeps restarting; Log Stream shows a database connection error at start-up | Wrong `DATABASE_URL`, often an unencoded special character in the password (an `@` splits the address at the wrong place), or missing `?sslmode=require` | URL-encode the password (`@` -> `%40`), check user, server, database name and `?sslmode=require`, save, restart |
| `{"detail":"Not Found"}` at `/` while `/api/health` works | An old image without the built website is still running | Check the image tag in **Deployment Center** matches the latest `sha-<commit>`; restart the Web App; re-run the CD deploy if needed |
| Site never answers, Log Stream shows "didn't respond to HTTP pings on port" | Port mismatch | Set `WEBSITES_PORT=8000` and restart |
| Start-up error "connection timed out" or "no pg_hba.conf entry" | PostgreSQL firewall | PostgreSQL server > **Networking**: tick **Allow public access from any Azure service within Azure to this server**; add your client IP to use pgAdmin |
| Draft with AI / Import from text show "The AI service could not ... right now" (502); logs show 401 | Wrong or expired `AZURE_OPENAI_API_KEY`, or the key belongs to another resource | Copy the key and endpoint from the same Azure OpenAI resource, save, restart |
| Same, logs show 404 "DeploymentNotFound" | `AZURE_OPENAI_DEPLOYMENT` is not the deployment name, or the endpoint is wrong | Use the exact deployment name from Azure AI Foundry; check the endpoint |
| AI drafts no longer cite the policy | Database is new or the policy was deleted | Upload the policy PDF again (see Data) |
| CD deploy job skipped | `AZURE_WEBAPP_NAME` variable not set | Add the repo variable and publish-profile secret |

**First step for every problem: open the Log Stream.** It shows the exact error.

## 7. Data

- **Seeding:** on start-up the app creates any missing tables (`create_all`) and, if the
  `items` table is empty, loads `data/sample_register.csv` (each record gets a `created`
  audit entry by "System"). It never overwrites existing data.
- **Policies on a new database:** policies are stored in the database, not in the image.
  On a new or reset database, upload `data/sample_policies/Vendor_Management_Policy.pdf`
  again with **Policies > Upload PDF** (Project Manager role).
- **Reset data** (deletes everything; only for demos and test environments): in pgAdmin run
  ```sql
  DROP TABLE IF EXISTS audit_log, policy_chunks, policy_documents, items;
  ```
  then restart the Web App. The tables are recreated, the sample register is loaded again,
  and the policy must be uploaded again. Locally with SQLite: stop the backend and delete
  `data/risk_register.db`.
- **Schema changes:** there are no migrations yet (`create_all` only adds missing tables, not
  new columns). A new column needs a manual `ALTER TABLE` or a reset.
- **One instance only:** the policy search index is built in memory from the database and is
  rebuilt only in the instance that received the upload or delete. With several instances,
  others would search stale policies. Keep the Web App at **one instance** (no scale-out).

## 8. Security notes

- **No login.** The role selector sends an `X-Role` header that anyone can change. It shows the
  workflow; it does not protect data. Use only synthetic data.
- **Keep the URL private.** Share it only with reviewers; do not post it in the repo, docs or
  screenshots.
- **Stop the Web App when not in use** (Web App > **Stop**) to limit access and cost. Start it
  again before a demo and allow a minute for start-up.
- **Never commit `.env`** or any key, password or connection string. `.env`, `*.db` and
  `venv` are in `.gitignore` and `.dockerignore`. If a secret is exposed,
  rotate it in Azure (regenerate the key or reset the password) and update the app settings.
