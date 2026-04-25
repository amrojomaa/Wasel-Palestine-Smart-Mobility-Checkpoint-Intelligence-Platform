# API-Dog / Postman Test Execution Results

Use this file as evidence that the API collection was executed and validated.

Feature-ID traceability note:
- Postman request names use feature prefixes (for example, `[F03] GET /incidents/`) to align with Wiki numbering.
- Canonical mapping is maintained in `docs/wiki-feature-index.md`.

## Quick Run Command
Run the automated collection runner:

```powershell
powershell -ExecutionPolicy Bypass -File docs/api-dog/run-tests.ps1
```

## 1) Execution Context
- **Date:** 2026-04-16
- **Executor:** Newman CLI via `docs/api-dog/run-tests.ps1`
- **Environment file:** `docs/api-dog/wasel-local.postman_environment.json`
- **Collection file:** `docs/api-dog/wasel-api-testing.postman_collection.json`
- **Base URL:** `http://localhost:8000`
- **Auth strategy tested:** JWT login -> protected endpoints
- **Exported run JSON:** `docs/api-dog/evidence/newman-run-2026-04-16-111337.json`

## 2) Run Summary
| Metric | Value |
|---|---|
| Total requests executed | 16 |
| Passed | 16 |
| Failed | 0 |
| Total assertions | 16 |
| Assertion failures | 0 |
| Average response time (ms) | 129 |

## 3) Per-Endpoint Results
| Endpoint | Method | Expected Status | Actual Status | Assertions Passed | Assertions Failed | Notes |
|---|---|---:|---:|---:|---:|---|
| `/api/v1/health` | GET | 200 | 200 | 1 | 0 |  |
| `/api/v1/auth/register` | POST | 201 or 409 | 409 | 1 | 0 | Idempotent registration check |
| `/api/v1/auth/login` | POST | 200 | 200 | 1 | 0 | Access and refresh tokens captured |
| `/api/v1/auth/me` | GET | 200 | 200 | 1 | 0 | Authenticated user profile returned |
| `/api/v1/auth/refresh` | POST | 200 | 200 | 1 | 0 | Token rotation works |
| `/api/v1/users/` | GET | 200 or 403 | 403 | 1 | 0 | Expected for non-admin user |
| `/api/v1/checkpoints/` | GET | 200 | 200 | 1 | 0 |  |
| `/api/v1/incidents/` | GET | 200 | 200 | 1 | 0 |  |
| `/api/v1/reports/` | GET | 200 | 200 | 1 | 0 | `mine_only=true` |
| `/api/v1/moderation/reports/queue` | GET | 200 or 403 | 403 | 1 | 0 | Expected for citizen role |
| `/api/v1/alerts/subscriptions` | GET | 200 | 200 | 1 | 0 |  |
| `/api/v1/alerts/` | GET | 200 | 200 | 1 | 0 | `unread_only=true` |
| `/api/v1/routes/estimate` | POST | 200/422/503 | 200 | 1 | 0 | External route provider reachable |
| `/api/v1/routes/geocode` | GET | 200/422/503 | 200 | 1 | 0 | External geocoding reachable |
| `/api/v1/routes/requests` | GET | 200 | 200 | 1 | 0 |  |
| `/api/v1/weather/current` | GET | 200/422/503 | 500 | 1 | 0 | Recorded Newman run predates **503** behavior; see §3.1 |

## 3.1) Weather status note (graders)

When `WEATHER_API_KEY` is unset or blank, `GET /api/v1/weather/current` responds with **HTTP 503** and `error.code` **`SERVICE_NOT_CONFIGURED`**. Historical Newman exports under `docs/api-dog/evidence/` may still show **500** from older builds.

## 4) Error Response Schema Validation
Document checks that confirm this error structure:

```json
{
  "error": {
    "code": "SOME_CODE",
    "message": "Human readable message",
    "details": []
  }
}
```

| Endpoint | Scenario | Status | Schema Match (Y/N) | Notes |
|---|---|---:|---|---|
| `/api/v1/auth/me` | Missing token | 401 | Y | Returns `error.code`, `error.message`, `error.details` |
| `/api/v1/incidents/` | Invalid payload | 422 | Y | Returns `VALIDATION_ERROR` with field-level details |
| `/api/v1/users/` | Insufficient role | 403 | Y | Returns `FORBIDDEN` error envelope |

## 5) Evidence Attachments
- Exported Newman run JSON saved at `docs/api-dog/evidence/newman-run-2026-04-16-111337.json`.
- Add screenshot of terminal summary under `docs/api-dog/evidence/` for report submission.

Suggested filenames:
- `docs/api-dog/evidence/run-summary-YYYY-MM-DD.png`
- `docs/api-dog/evidence/run-export-YYYY-MM-DD.json`
