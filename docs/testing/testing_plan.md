# Wasel Palestine Testing Plan

## 1) Test Pyramid
- **Unit tests**: validate isolated logic (security, schemas, cache, scoring/dedup rules).
- **Integration tests**: validate API contracts, auth behavior, dependency injection, error handling.
- **Performance tests (k6)**: validate latency, throughput, and stability under realistic load patterns.

## 2) Unit Test Scope
- Token creation/validation and token type enforcement.
- Input schema validation (location ranges, route constraints, enum constraints).
- Cache TTL behavior and edge cases.
- Service-level business rules (duplicate detection logic, confidence scoring once implemented).

## 3) Integration Test Scope
- `/api/v1/health` liveness.
- Auth endpoints (`/auth/login`, `/auth/me`) with mocks/overrides.
- External integration endpoints (`/routes/estimate`, `/weather/current`) with service mocking.
- Error path validation (422 payload validation, 401 missing token, 403 role restrictions).

## 4) API Contract Tests (API-Dog)
- Use imported collection in `docs/api-dog/wasel-api-testing.postman_collection.json`.
- Maintain environment vars in `docs/api-dog/wasel-local.postman_environment.json`.
- Track baseline status codes, schema shape, and auth flow.
- Save run evidence in `docs/api-dog/test-execution-results.md`.

## 5) Performance Strategy (k6)
- **Read-heavy**: incident listing under filter/sort/pagination pressure.
- **Write-heavy**: report submission throughput and validation overhead.
- **Mixed**: concurrent read/write using weighted scenarios.
- **Spike**: sudden traffic surges for autoscaling and queue saturation behavior.
- **Soak**: long-duration stability and memory/resource leak detection.

## 6) CI Recommendation
- Run unit + integration tests on each PR.
- Run lightweight k6 smoke profile nightly.
- Run full spike/soak before milestone demos.
