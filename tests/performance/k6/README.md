# k6 Performance Test Suite

## Prerequisites
- k6 installed locally
- Running backend instance
- Valid JWT access token for protected endpoints
- Seeded database (recommended before benchmarking read/query paths)

## Environment variables
- `BASE_URL` (default: `http://localhost:8000`)
- `ACCESS_TOKEN` (optional for public endpoints, required for protected endpoints)
- `ACCESS_TOKENS` (optional comma-separated token pool used for write-heavy/mixed/soak scripts)
- `SOAK_INCLUDE_WRITES` (`true/false`, default: `false`)

## Seed realistic dataset (recommended)
```bash
python -m tests.performance.seed_performance_data --incidents 1000 --reports 1000 --alerts 500
```

## Run scripts
```bash
k6 run tests/performance/k6/incidents_read_heavy.js
k6 run tests/performance/k6/reports_write_heavy.js
k6 run tests/performance/k6/mixed_workload.js
k6 run tests/performance/k6/spike_test.js
k6 run tests/performance/k6/soak_test.js
```

Run a full soak (45 minutes):
```bash
k6 run --vus 25 --duration 45m tests/performance/k6/soak_test.js
```

## JSON output example
```bash
k6 run --out json=results/incidents_read_heavy.json tests/performance/k6/incidents_read_heavy.js
```
