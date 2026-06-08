# TIDES AI Startup Evaluation Platform

Phase 1 backend foundation for TIDES IIT Roorkee startup screening and incubation assessment.

This implementation intentionally does **not** include AI agents, LiteLLM, Qdrant, n8n, or report generation yet. It focuses on the enterprise platform base: FastAPI, PostgreSQL, SQLAlchemy 2.x, Alembic, JWT auth, RBAC, startup intake, lifecycle tracking, canonical startup profiles, source attribution, evaluation schema, deterministic recommendation rules, audit logging, and committee support.

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- JWT authentication
- Docker and Docker Compose

## Quick Start

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Update `JWT_SECRET_KEY` in `.env`.

3. Start the stack:

```bash
docker compose up --build
```

4. Open the API:

- OpenAPI docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

5. Bootstrap the first admin:

```bash
curl -X POST http://localhost:8000/api/v1/auth/bootstrap-admin \
  -H "Content-Type: application/json" \
  -d '{"name":"TIDES Admin","email":"admin@tides.local","password":"ChangeMeStrong123!"}'
```

6. Log in:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tides.local","password":"ChangeMeStrong123!"}'
```

Use the returned bearer token in `Authorization: Bearer <token>`.

## Local Development Without Docker

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Role-Based Access Control

Roles:

- `admin`
- `evaluator`
- `committee_member`
- `viewer`

The first admin is created through `/api/v1/auth/bootstrap-admin`. After that, only admins can create or update users.

## Core API Areas

- Authentication: `/api/v1/auth`
- Users: `/api/v1/users`
- Startup intake and lifecycle: `/api/v1/startups`
- Startup Profile and versions: `/api/v1/startups/{startup_id}/profile`
- Founders: `/api/v1/startups/{startup_id}/founders`
- Company Profile: `/api/v1/startups/{startup_id}/company-profile`
- Documents: `/api/v1/startups/{startup_id}/documents`
- Document Sources: `/api/v1/startups/{startup_id}/document-sources`
- Evaluation Rubrics: `/api/v1/evaluation-rubrics`
- Evaluations: `/api/v1/startups/{startup_id}/evaluations`
- Recommendation Rules: `/api/v1/admin/recommendation-rules`
- Reviewer Comments: `/api/v1/evaluations/{evaluation_id}/comments`
- Committee Notes: `/api/v1/evaluations/{evaluation_id}/committee-notes`
- Score Overrides: `/api/v1/evaluation-scores/{score_id}/override`
- Audit Logs: `/api/v1/audit-logs`

## Startup Lifecycle Statuses

- Draft
- Submitted
- Under Review
- AI Evaluated
- Committee Review
- Recommended
- Conditionally Recommended
- Not Recommended
- Incubated
- Graduated
- Archived

Every status change creates records in both `startup_status_history` and `audit_logs`.

## Recommendation Rules

Recommendations are deterministic and threshold based. Seed defaults after logging in as admin:

```bash
curl -X POST http://localhost:8000/api/v1/admin/recommendation-rules/defaults \
  -H "Authorization: Bearer <token>"
```

Default bands:

- 80-100: Recommended
- 65-79.99: Committee Review
- 50-64.99: Conditionally Recommended
- 0-49.99: Not Recommended

## Tests

```bash
pytest
```
