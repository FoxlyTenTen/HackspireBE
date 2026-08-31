# HACKSPIRE: LUMINA — Backend API

FastAPI backend for the HACKSPIRE: LUMINA hackathon platform. Backend only — the
deliverable is the API plus its auto-generated Swagger documentation.

## Run locally

```bash
# 1. (once) create a venv and install dependencies
python -m venv venv
venv\Scripts\pip install -r requirements.txt

# 2. run the server
venv\Scripts\uvicorn app.main:app --reload
```

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- Base path for all endpoints: `/api/v1`

## Configuration

Copy `.env.example` to `.env` and adjust. Key settings:

| Variable | Default | Notes |
| --- | --- | --- |
| `DATABASE_URL` | *(unset)* | Supabase Postgres URL in production. If unset, the app falls back to a local SQLite file `./hackspire.db` — no external service needed. `postgresql://` URLs are automatically upgraded to `postgresql+asyncpg://`. |
| `JWT_SECRET` | `change-me-in-production` | HS256 signing secret. |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | `admin@hackspire.dev` / `admin123` | A bootstrap admin account is created on startup if no admin exists. |
| `UPLOAD_DIR` | `./uploads` | Local disk storage for materials, behind an interface swappable for Supabase Storage. |

Tables are created automatically on startup (`create_all`) — no migration step.

## Auth flow

1. `POST /api/v1/auth/login` with `{username, password}` — username is the email
   **or** student/staff ID. Returns `{jwt, first_login}`.
2. If `first_login` is `true`, the account must call
   `POST /api/v1/auth/change-password` before any other endpoint (everything else
   returns 403 until then), then log in again.
3. Send `Authorization: Bearer <jwt>` on every request. Guard levels:
   participant (any logged-in user), team leader (leader of the team in the
   path) and admin.

Participants are provisioned by an admin via the two-step Excel import
(`POST /api/v1/admin/participants/import` to preview, then `/import/confirm` to
create accounts). The expected sheet header is `name, email, student_staff_id`;
the initial password is the student/staff ID.

All error responses share the shape `{"error": "<message>"}`.

## Run with Docker

```bash
docker build -t hackspire-backend .
docker run -p 8080:8080 hackspire-backend
```
Runs against the SQLite fallback unless you pass `-e DATABASE_URL=...` (and the
other env vars from the Configuration table above) at `docker run` time.

## Running tests

```bash
pip install -r requirements.txt
pytest
```
Runs the smoke test in `tests/` only (pytest.ini scopes discovery to that
folder so it doesn't pick up `app/test_db_connection.py`, which is a manual
script, not an automated test). The GitHub Actions workflow runs this same
`pytest` step in a `test` job before deploying — the deploy job only runs if
tests pass.

## Deploying via GitHub Actions (one-time GCP setup)

`.github/workflows/deploy-backend.yml` builds and deploys `app/` to a Cloud
Run service on every push to `main` that touches `app/**`, `requirements.txt`,
or `Dockerfile` — pushes touching only `frontend/` never trigger it. Uses
keyless Workload Identity Federation (WIF), no JSON service account key is
ever stored in GitHub.

Use a **new GCP project**, separate from any other demo project. Run
everything below **once**, replacing the placeholders first:

```
PROJECT_ID=your-gcp-project-id
REGION=us-central1
GITHUB_REPO=your-github-username/HackSpireBE
SERVICE_ACCOUNT_NAME=hackspire-deployer
POOL_NAME=hackspire-pool
PROVIDER_NAME=hackspire-provider
REPO_NAME=hackspire-images
```

### 1. Install/auth the gcloud CLI and select your project
```
gcloud auth login
gcloud config set project $PROJECT_ID
```

### 2. Enable the required APIs
```
gcloud services enable run.googleapis.com artifactregistry.googleapis.com iamcredentials.googleapis.com cloudresourcemanager.googleapis.com
```

### 3. Create an Artifact Registry repo (holds the Docker images)
```
gcloud artifacts repositories create $REPO_NAME --repository-format=docker --location=$REGION
```

### 4. Create the deploy service account
```
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME --display-name="GitHub Actions deployer"
```

### 5. Grant that service account the roles it needs
```
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

### 6. Create a Workload Identity Pool
```
gcloud iam workload-identity-pools create $POOL_NAME --location="global" --display-name="GitHub Actions pool"
```

### 7. Create a Workload Identity Provider inside that pool, trusting GitHub OIDC
```
gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME \
  --location="global" \
  --workload-identity-pool=$POOL_NAME \
  --display-name="GitHub provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${GITHUB_REPO}'" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### 8. Allow that specific GitHub repo to impersonate the service account
```
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud iam service-accounts add-iam-policy-binding \
  "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${GITHUB_REPO}"
```

### 9. Get the full Workload Identity Provider resource name
```
gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
  --location="global" \
  --workload-identity-pool=$POOL_NAME \
  --format="value(name)"
```
Copy the output — it looks like:
`projects/123456789/locations/global/workloadIdentityPools/hackspire-pool/providers/hackspire-provider`

### 10. Add GitHub repo secrets and variables
In this repo on GitHub: **Settings → Secrets and variables → Actions**

- **Secrets** (tab: *Secrets*) — values come from your Supabase project dashboard
  and your own `.env`, not gcloud output (except the first two):

  | Name | Value |
  |---|---|
  | `GCP_WORKLOAD_IDENTITY_PROVIDER` | the resource name from step 9 |
  | `GCP_SERVICE_ACCOUNT` | `hackspire-deployer@<PROJECT_ID>.iam.gserviceaccount.com` |
  | `DATABASE_URL` | your Supabase Postgres connection string |
  | `JWT_SECRET` | from `.env` |
  | `JWT_EXPIRES_MIN` | from `.env` |
  | `ADMIN_EMAIL` | from `.env` |
  | `ADMIN_PASSWORD` | from `.env` |
  | `ADMIN_NAME` | from `.env` |
  | `ADMIN_STUDENT_STAFF_ID` | from `.env` |
  | `SUPABASE_URL` | from `.env` |
  | `SUPABASE_ANON_KEY` | from `.env` |
  | `SUPABASE_SERVICE_ROLE_KEY` | from `.env` |
  | `SUPABASE_JWT_SECRET` | from `.env` |
  | `FRONTEND_URL` | your deployed frontend's URL once it exists (placeholder ok for now) |
  | `PARTICIPANT_CAP` | from `.env` |
- **Variables** (tab: *Variables*):

  | Name | Value |
  |---|---|
  | `GCP_PROJECT_ID` | your project id |
  | `GCP_REGION` | e.g. `us-central1` |

### 11. Push to trigger the deploy
```
git add Dockerfile .dockerignore requirements.txt pytest.ini tests/ .github/workflows/deploy-backend.yml README.md
git commit -m "Add Docker + CI/CD for backend"
git push
```
Then check the **Actions** tab on GitHub — the workflow should run `test`
then `deploy`, finishing with a Cloud Run service URL printed in the "Deploy
to Cloud Run" step.

> The workflow deploys with `--allow-unauthenticated`, so the resulting URL
> is publicly reachable — fine for a hackathon demo, but tighten this
> (`roles/run.invoker` bound to specific members) before treating it as
> production.
