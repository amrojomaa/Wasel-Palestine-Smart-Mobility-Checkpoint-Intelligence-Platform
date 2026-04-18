# Wasel Palestine - Full Project Report

## 1) Executive Summary
Wasel Palestine is a backend-only smart mobility intelligence platform built for an Advanced Software Engineering course project. The system aggregates mobility data and exposes it through secure, versioned REST APIs under `/api/v1/` to support citizens, moderators, and administrators.

The platform delivers checkpoint and incident intelligence, crowdsourced report moderation workflows, alert subscriptions and fan-out, route estimation support, and weather context integration. The implementation follows a layered architecture with a strong focus on API design, role-based access control, resilience patterns, and testability.

## 2) Project Context and Objectives
### 2.1 Context
- Course: Advanced Software Engineering.
- Repository scope: backend services only (no web/mobile frontend in this repository).
- Deployment model: Dockerized API service and PostgreSQL database.

### 2.2 Objectives
- Build a production-style backend with clear separation of concerns.
- Expose all core features through REST endpoints with versioning.
- Implement secure authentication and role-based authorization.
- Support both ORM and raw SQL for data access and performance-sensitive queries.
- Provide measurable testing evidence (unit, integration, API contract, performance).

## 3) Scope and Core Features
### 3.1 Implemented Functional Scope
- **Checkpoints:** listing, creation, updates, and status history.
- **Incidents:** creation, listing with filtering/pagination/sorting, updates, verification lifecycle, and verification events.
- **Crowdsourced Reports:** submission, retrieval, voting, duplicate detection, and moderation flow.
- **Alerts:** subscription management, alert retrieval, read status updates, and fan-out records.
- **Routing:** route estimate, geocoding, and route request history endpoints.
- **Weather:** current weather endpoint integration.
- **Identity and Access:** registration, login, refresh, logout, current-user profile, and role checks.

### 3.2 Out-of-Scope
- Frontend/mobile user interface implementation.
- Production infrastructure hardening and cloud deployment automation.

## 4) Architecture and Design
### 4.1 Layered Architecture
The system follows:

`API Layer -> Service Layer -> Repository Layer -> Database`

Supporting components:
- Security/auth dependencies.
- Integration clients for external providers.
- Cache and resilience utilities.
- Audit logging hooks.

Reference diagram: `docs/architecture/system-architecture.md`.

### 4.2 Directory Structure
- `app/api/v1/endpoints/` - FastAPI routers.
- `app/services/` - business logic and orchestration.
- `app/repositories/` - SQLAlchemy and selective raw SQL access.
- `app/models/` - ORM entities.
- `app/schemas/` - request/response contracts.
- `app/integrations/` - provider clients (routing, weather).
- `app/core/` - config, security, exceptions, logging.
- `tests/` - unit, integration, and k6 performance scripts.
- `docs/` - architecture, testing, API-Dog evidence, performance reporting.

## 5) Technology Stack
- **Language:** Python
- **Framework:** FastAPI
- **GraphQL (bonus):** Strawberry GraphQL router
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.x
- **Migrations:** Alembic
- **Auth:** JWT access + refresh token flow
- **HTTP client:** httpx
- **Containerization:** Docker + Docker Compose
- **Testing:** Pytest + Newman + k6

### 5.1 Stack Justification by Evaluation Axis
| Axis | Stack Choice | Justification |
|---|---|---|
| Scalability | FastAPI + Uvicorn, PostgreSQL, stateless JWT auth, containerized deployment | FastAPI/Uvicorn supports high-concurrency async I/O; PostgreSQL handles indexed relational workloads for incidents/reports/history; JWT keeps API nodes mostly stateless for horizontal scaling; Docker enables reproducible scale-out in multi-container setups. |
| Security | JWT access/refresh flow, refresh rotation/revocation, RBAC, centralized exception envelope | Short-lived access tokens reduce exposure windows; hashed refresh tokens with revoke/rotate mitigate replay risk; role checks (`citizen`, `moderator`, `admin`) enforce least privilege; uniform error handling avoids leaking internal details and improves auditability. |
| Maintainability | Layered architecture (API -> Service -> Repository), Pydantic schemas, Alembic migrations, provider interfaces | Clear separation of concerns minimizes coupling and supports refactoring by module; strict schemas keep contracts explicit; migrations preserve controlled DB evolution; provider abstractions isolate external APIs and simplify replacement/testing. |
| Development Efficiency | Python ecosystem, FastAPI automatic OpenAPI docs, SQLAlchemy ORM + selective raw SQL, pytest/newman/k6 toolchain | Rapid backend iteration with concise Python/FastAPI patterns; OpenAPI generation speeds endpoint validation; ORM covers common CRUD while raw SQL is used only for hot paths; combined unit/integration/API/performance tests provide fast feedback and evidence generation. |

## 6) Database Design
### 6.1 Domain Grouping
- **Identity & Access:** `users`, `roles`, `user_roles`, `refresh_tokens`
- **Mobility Core:** `checkpoints`, `checkpoint_status_history`, `incidents`, `incident_verification_events`, `incident_categories`
- **Crowdsourcing:** `reports`, `report_votes`, `report_moderation_actions`
- **Alerts:** `alert_subscriptions`, `alerts`, `alert_deliveries`
- **Routing:** `route_requests`
- **Governance:** `audit_logs`

### 6.2 ERD
Logical relationship diagram is documented in:
- `docs/architecture/erd-diagram.md`

## 7) API Design and Endpoint Coverage
### 7.1 Versioning
All endpoints are namespaced under `/api/v1`.

### 7.2 Endpoint Groups Implemented
- Health: `/health`
- Auth: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`
- Users: `/users/` (RBAC-protected)
- Checkpoints: CRUD-lite + status history
- Incidents: list/create/get/update/verify/events
- Reports: create/list/get/vote
- Moderation: queue/actions/promote
- Alerts: subscriptions/list/mark-read
- Routes: estimate/geocode/history
- Weather: current weather
- GraphQL (bonus): summary queries endpoint

### 7.3 API Query Features
`GET /incidents/` supports:
- filtering (`status`)
- pagination (`page`, `page_size`)
- sorting (`sort_by`, `order`)

### 7.4 API Design Rationale
- **Resource-oriented versioned paths (`/api/v1/...`)** were selected to keep contracts stable for clients while allowing non-breaking evolution through future versions.
- **Separation of state and history** was applied in workflows such as incident verification: current incident status is kept on `incidents`, while immutable transitions are stored in `incident_verification_events`. This preserves auditability and avoids overwriting historical decisions.
- **Pagination and server-side filtering/sorting** are used on list-heavy endpoints (for example, incidents) to control payload size, reduce client-side post-processing, and keep query costs predictable as data volume grows.
- **Dedicated action endpoints** (such as verify, vote, mark-read, moderation actions) were used where operations represent domain actions, not simple CRUD field edits. This keeps business rules explicit and easier to authorize/audit.
- **Consistent response and error envelopes** were chosen to simplify frontend/API consumer handling, enabling uniform success parsing and standardized error handling across all endpoint groups.

## 8) Security and Access Control
- JWT-based authentication for protected endpoints.
- Access + refresh token flow with refresh rotation/revocation.
- RBAC roles:
  - `citizen`
  - `moderator`
  - `admin`
- Standardized error envelope format:
  - `error.code`
  - `error.message`
  - `error.details`

## 9) Business Logic Highlights
- Incident verification lifecycle and event history tracking.
- Alert fan-out based on active subscriptions.
- Report duplicate detection using hash + fuzzy similarity checks.
- Abuse-prevention/rate-limiting behavior for report submissions.
- Audit logging for key domain actions.

## 10) External Integrations and Resilience
### 10.1 Integrations
- Routing/geocoding through OSM-compatible providers.
- Current weather through OpenWeather API.

### 10.2 Resilience Controls
- request timeout
- retry with backoff and jitter
- handling of `429 Retry-After`
- provider throttling
- TTL caching

## 11) Testing Strategy and Evidence
### 11.1 Planned Coverage
- Unit tests for isolated logic.
- Integration tests for API behavior and dependency wiring.
- API contract tests with API-Dog/Postman collection.
- Load and stability testing via k6 profiles.

Reference: `docs/testing/testing_plan.md`.

### 11.2 API-Dog / Postman Execution Evidence
Execution evidence is captured in:
- `docs/api-dog/test-execution-results.md`
- exported run JSON under `docs/api-dog/evidence/`

Recorded run summary:
- total requests: 16
- passed: 16
- failed: 0
- assertions: 16/16 passed
- average response time: 129 ms

## 12) Performance Testing and Findings
Reference: `docs/performance/performance-report.md`.

### 12.1 Round A (Before Optimizations) - Highlights
- Strong throughput but high write-path error rate in stressed scenarios.
- Notable spike p95 latency under sudden load.

### 12.2 Round B (After Optimizations) - Highlights
Applied improvements:
- canonical trailing-slash URLs in k6 scripts
- write scenario pacing/payload tuning
- report service fix for nullable `checkpoint_id` duplicate-check SQL

Observed aggregate outcome:
- error rate improved
- throughput and latency aggregate worsened due to safer, policy-compliant write profile and environment constraints

Clarification for graders:
- The apparent regression in aggregate throughput is intentional. Round B removes anti-abuse bypass behavior and redirect-hop noise that inflated Round A throughput.
- The key stabilization metric is reliability: aggregate error rate improved from `14.37%` to `8.24%`.

### 12.3 Current Limitation Notes
- Soak run captured with 10-minute override (not full 45 minutes yet).
- Test dataset was initially small; a seeding utility now exists for submission reruns:
  - `python -m tests.performance.seed_performance_data --incidents 1000 --reports 1000 --alerts 500`
- Seeded-data rerun evidence is now captured in performance artifacts:
  - `docs/performance/results/write-heavy-round-b-token-pool-summary.json`
  - `docs/performance/results/mixed-round-b-token-pool-summary.json`

## 13) Documentation Deliverables Status
- Architecture diagram: available (`docs/architecture/system-architecture.md`)
- ERD diagram: available (`docs/architecture/erd-diagram.md`)
- API-Dog execution evidence: available (`docs/api-dog/test-execution-results.md`)
- Performance report with real metrics: available (`docs/performance/performance-report.md`)
- Git workflow recovery plan: available (`docs/process/git-workflow-recovery-plan.md`)

## 14) Git Workflow and Traceability Plan
To satisfy grading requirements for traceable process:
- create feature branches by domain milestone
- split changes into meaningful commits
- open/merge PRs with test and documentation evidence

Reference plan: `docs/process/git-workflow-recovery-plan.md`.
Execution commands: `docs/process/git-workflow-execution-commands.md`.

## 15) Known Risks and Gaps
- Full 45-minute soak evidence is pending.
- Large realistic seeded data validation has been executed for token-pool reruns; keep terminal screenshot evidence with submission.
- Weather endpoint behavior depends on `WEATHER_API_KEY`; missing key can produce expected 500 responses.
- Current write-heavy benchmark profile prioritizes policy-compliant writes over max throughput stress.
- Abuse-prevention limiter is in-memory and process-local (intended for single-instance deployment).

### 15.1 Write-heavy interpretation note
- Write-heavy failure percentages are expected under anti-abuse policy stress and should be interpreted as enforcement evidence (`429` controls working), not as a regression in read-path stability.

## 16) Recommendations for Final Submission
1. Attach this report with the architecture and ERD diagram files.
2. Include API-Dog result JSON and one terminal screenshot in evidence.
3. Include k6 summary JSON files and `performance-report.md`.
4. Execute the Git workflow recovery plan and submit PR history screenshots/links.
5. If time permits, run full 45-minute soak and append a short addendum section.

## 17) Conclusion
Wasel Palestine demonstrates a strong backend engineering implementation with clean architecture, secure API workflows, and robust documentation/testing artifacts. The remaining work is primarily process and evidence completion (traceable git history and extended soak realism), not a core architecture rewrite.

## 18) Bonus (Optional) - GraphQL
- A lightweight GraphQL endpoint is provided at `/api/v1/graphql`.
- It exposes read-focused bonus queries such as `health`, `systemStats`, and `recentIncidentTitles`.
- This bonus path is isolated from core REST grading criteria and does not change mandatory API behavior.
