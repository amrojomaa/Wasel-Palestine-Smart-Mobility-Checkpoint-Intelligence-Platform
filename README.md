# Wasel Palestine Backend

Backend-only smart mobility intelligence platform for Palestine, designed for the Advanced Software Engineering course project.

The system aggregates mobility-related data (checkpoints, incidents, route constraints, weather context) and exposes it through versioned REST APIs under `/api/v1/`.

## Project Overview

Wasel Palestine is an API-centric backend that helps users navigate movement challenges by providing reliable and structured mobility intelligence.

The platform focuses on:
- checkpoint and incident intelligence
- crowdsourced reporting and moderation workflows
- route estimation with contextual factors
- alert subscriptions and notification-ready records
- resilient integration with external routing and weather providers

UI/mobile clients are out of scope in this repository.

## Objectives

- Build a production-style backend using professional architecture and development practices.
- Expose all system capabilities via secure, versioned REST APIs.
- Use a relational database with both ORM-based operations and selected raw SQL for performance-critical queries.
- Support role-based workflows for citizens, moderators, and admins.
- Handle external service instability through timeouts, retries, throttling, and caching.
- Validate correctness and non-functional behavior with automated testing and load testing.

## Architecture

### High-level components

- **API Layer**: FastAPI routers under `/api/v1/`.
- **Service Layer**: Business logic (auth, routing/weather orchestration, moderation-ready service boundaries).
- **Repository Layer**: SQLAlchemy data access + selective raw SQL.
- **Integration Layer**: Provider interfaces + concrete implementations (OSM routing/geocoding, weather API).
- **Security Layer**: JWT access + refresh, RBAC, request validation, centralized error handling.
- **Infrastructure Layer**: Dockerized API + PostgreSQL.

### Current technical stack

- **Framework**: FastAPI
- **Language**: Python
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.x
- **Migrations**: Alembic (initial schema migration included)
- **Auth**: JWT (access + refresh)
- **External HTTP**: `httpx` with resilience controls
- **Containerization**: Docker + Docker Compose
- **Testing**: Pytest + k6

### Why this stack

- **Scalability**: FastAPI/Uvicorn async handling + stateless JWT auth and PostgreSQL indexing support high-concurrency API workloads.
- **Security**: JWT access/refresh with rotation/revocation and RBAC (`citizen`, `moderator`, `admin`) enforce secure access control.
- **Maintainability**: Layered architecture (`API -> Service -> Repository`) and typed schemas keep module boundaries and contracts clear.
- **Development efficiency**: FastAPI OpenAPI generation, SQLAlchemy productivity, and pytest/newman/k6 coverage speed implementation and validation.

## Database Schema Summary

The full academic schema is designed around these core domains:

- **Identity & Access**: `users`, `roles`, `user_roles`, `refresh_tokens`
- **Mobility Core**: `checkpoints`, `checkpoint_status_history`, `incidents`, `incident_verification_events`, `incident_categories`
- **Crowdsourcing**: `reports`, `report_moderation_actions`, `report_votes`
- **Alerts**: `alert_subscriptions`, `alerts`, `alert_deliveries`
- **Routing Intelligence**: `route_requests`
- **Governance**: `audit_logs`

Implemented relationships include one-to-many status/verification histories, many-to-many user roles, report credibility voting, and subscription-driven alert fan-out.

## Setup Instructions (Local)

### 1) Prerequisites

- Python 3.12+ recommended
- PostgreSQL 16+ (if running without Docker)
- Docker Desktop (recommended)

### 2) Clone and configure

```bash
cp .env.example .env
```

Edit `.env` values:
- `SECRET_KEY`
- `DATABASE_URL`
- optional seed admin credentials (`SEED_ADMIN_*`)
- external provider configuration (`ROUTING_*`, `WEATHER_*`)
- set `WEATHER_API_KEY` for `GET /api/v1/weather/current`; if it is unset or empty, that route returns **HTTP 503** with `error.code` `SERVICE_NOT_CONFIGURED` (not a generic 500)

### 3) Install dependencies (local mode)

```bash
pip install -r requirements.txt
```

For test dependencies:

```bash
pip install -r requirements-dev.txt
```

### 3.1) Run migrations

```bash
alembic upgrade head
```

Rollback one revision:

```bash
alembic downgrade -1
```

### 4) Run application

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Docker Usage

Build and start services:

```bash
docker compose up --build
```

Services:
- `api` on `http://localhost:8000`
- `db` (PostgreSQL) on `localhost:5432`

Stop services:

```bash
docker compose down
```

Persistent PostgreSQL volume is managed via `postgres_data`.

## API Overview

All endpoints are versioned under:

```text
/api/v1
```

### Implemented endpoint groups

- Health: `/health`
- Authentication:
  - `POST /auth/register`
  - `POST /auth/login`
  - `POST /auth/refresh`
  - `POST /auth/logout`
  - `GET /auth/me`
- Users (RBAC sample): `GET /users/` (admin-only)
- Checkpoints:
  - `GET /checkpoints/`
  - `POST /checkpoints/`
  - `GET /checkpoints/{checkpoint_id}`
  - `PATCH /checkpoints/{checkpoint_id}`
  - `GET /checkpoints/{checkpoint_id}/status-history`
  - `POST /checkpoints/{checkpoint_id}/status-history`
- Incidents:
  - `GET /incidents/` (supports `status`, `page`, `page_size`, `sort_by`, `order`)
  - `POST /incidents/`
  - `GET /incidents/{incident_id}`
  - `PATCH /incidents/{incident_id}`
  - `POST /incidents/{incident_id}/verify`
  - `GET /incidents/{incident_id}/verification-events`
- Reports:
  - `POST /reports/`
  - `GET /reports/`
  - `GET /reports/{report_id}`
  - `POST /reports/{report_id}/vote`
- Moderation:
  - `GET /moderation/reports/queue`
  - `POST /moderation/reports/{report_id}/actions`
  - `POST /moderation/reports/{report_id}/promote-to-incident`
- Alerts:
  - `GET /alerts/subscriptions`
  - `POST /alerts/subscriptions`
  - `DELETE /alerts/subscriptions/{subscription_id}`
  - `GET /alerts/` (supports unread and subscription filtering)
  - `POST /alerts/{alert_id}/mark-read`
- Routing integration:
  - `POST /routes/estimate`
  - `GET /routes/geocode`
  - `GET /routes/requests`
- Weather integration:
  - `GET /weather/current`
- GraphQL:
  - `POST /graphql`

## Authentication Flow (JWT Access + Refresh)

1. User logs in via `POST /api/v1/auth/login`.
2. API returns:
   - short-lived `access_token`
   - long-lived `refresh_token`
3. Client uses `Authorization: Bearer <access_token>` for protected endpoints.
4. When access token expires, client calls `POST /api/v1/auth/refresh`.
5. Refresh token rotation and revocation are enforced on refresh/logout.

RBAC is applied via role checks:
- `citizen`
- `moderator`
- `admin`

## External Integrations

### 1) Routing/Geolocation (OpenStreetMap-based)

- Routing provider: OSRM-compatible endpoint
- Geocoding provider: Nominatim
- Abstracted via provider interface for future replacement

### 2) Weather

- OpenWeather current weather endpoint
- API key managed via environment variable (`WEATHER_API_KEY`)
- Startup logs warn when the key is missing or blank; requests to `/api/v1/weather/current` then receive **HTTP 503** `SERVICE_NOT_CONFIGURED`

### 3) GraphQL

- Optional GraphQL endpoint available at `/api/v1/graphql`
- Useful for flexible read queries over summary data

Sample query:

```graphql
query {
  health
  systemStats {
    checkpoints
    incidents
    reports
  }
  recentIncidentTitles(limit: 5)
}
```

### Resilience controls

- request timeout
- retry with exponential backoff + jitter
- 429 `Retry-After` handling
- provider-level throttle intervals
- response caching with TTL
- partial route constraint handling with documented heuristic penalties for `avoid_checkpoints` and `avoid_area_ids` (OSRM public limitation)

## Testing Strategy

Testing assets are available under `tests/` and `docs/testing/`.

- **Unit tests**: token/security utilities, schema validation, cache behavior, abuse-prevention throttling
- **Integration tests**: API routes with dependency overrides and service mocking, including incidents/moderation/alerts/route history
- **API contract tests**: sample API-Dog/Postman-compatible collection and environment files

Run tests:

```bash
pytest
```

Reference:
- `docs/testing/testing_plan.md`
- `docs/api-dog/wasel-api-testing.postman_collection.json`
- `docs/api-dog/wasel-local.postman_environment.json`
- `docs/api-dog/test-execution-results.md`
- `docs/api-dog/run-tests.ps1`

## Performance Testing

Performance scripts are provided using k6:

- `tests/performance/k6/incidents_read_heavy.js`
- `tests/performance/k6/reports_write_heavy.js`
- `tests/performance/k6/mixed_workload.js`
- `tests/performance/k6/spike_test.js`
- `tests/performance/k6/soak_test.js`

Run example:

```bash
k6 run tests/performance/k6/incidents_read_heavy.js
```

Seed realistic dataset before benchmarking:

```bash
python -m tests.performance.seed_performance_data --incidents 1000 --reports 1000 --alerts 500
```

For write-heavy/mixed/soak tests, prefer a token pool:

```bash
ACCESS_TOKENS="<token1>,<token2>,<token3>,<token4>" k6 run tests/performance/k6/reports_write_heavy.js
```

Report templates:
- `docs/performance/performance-report-template.md`
- `docs/performance/performance-report.md`

Required reporting metrics:
- average response time
- p95 latency
- throughput
- error rate
- bottlenecks and root causes
- before/after optimization comparison

## Documentation Deliverables

This repository is structured to support the course deliverables:

- System overview and architecture
- Architecture diagram: `docs/architecture/system-architecture.md`
- ERD diagram: `docs/architecture/erd-diagram.md`
- API design and authentication flow
- External integration strategy and resilience approach
- API contract test execution evidence: `docs/api-dog/test-execution-results.md`
- Testing strategy (unit/integration/API contract)
- k6 performance scenarios and reporting templates

## Submission Alignment Checklist

- Repository description matches project scope (backend API, mobility intelligence, auth/RBAC, integrations, testing evidence).
- `.env.example` clearly marks weather API requirement (`WEATHER_API_KEY`) for `/api/v1/weather/current` (missing key → HTTP **503** `SERVICE_NOT_CONFIGURED`).
- `.gitignore` excludes local SQLite (`local-dev.db`), Python caches, `.pytest_cache`, and bundled `k6` binaries under `tools/k6/` from accidental commits.
- Performance report includes seeded-data proof and token-pool rerun metrics:
  - `docs/performance/performance-report.md`
  - `docs/performance/results/write-heavy-round-b-token-pool-summary.json`
  - `docs/performance/results/mixed-round-b-token-pool-summary.json`
- Final report references performance and API-Dog evidence consistently:
  - `docs/full-project-report.md`
  - `docs/api-dog/test-execution-results.md`

## Project Structure (Current)

```text
app/
  api/v1/endpoints/      # versioned REST endpoints
  core/                  # config, security, exceptions, logging
  db/                    # engine/session/base wiring
  dependencies/          # auth/RBAC dependencies
  integrations/          # provider interfaces + concrete clients
  models/                # SQLAlchemy models
  repositories/          # ORM/raw SQL data access
  schemas/               # request/response contracts
  services/              # business/use-case logic
  utils/                 # shared utility components
tests/
  unit/
  integration/
  performance/k6/
docs/
  api-dog/
  testing/
  performance/
```

## Status

The repository now includes:
- production-style backend architecture
- implemented core domain modules (checkpoints/incidents/reports/moderation/alerts/routes)
- external integrations with resilience controls
- audit logging hooks for key domain actions
- anti-abuse protections for report submission
- anti-abuse protections are process-local by design (single-instance scope)
- Alembic initial schema migration
- unit/integration/k6 testing assets and documentation deliverables
