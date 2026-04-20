# Wasel Palestine Performance Report Template

## 1) Test Context
- **Build/Commit:**
- **Date:**
- **Environment:** (local/docker/staging)
- **Database size:**
- **k6 version:**
- **Endpoints under test:**

## 2) Workloads Executed
| Scenario | Script | VUs | Duration | Notes |
|---|---|---:|---:|---|
| Read-heavy incidents | `tests/performance/k6/incidents_read_heavy.js` |  |  |  |
| Write-heavy reports | `tests/performance/k6/reports_write_heavy.js` |  |  |  |
| Mixed workload | `tests/performance/k6/mixed_workload.js` |  |  |  |
| Spike test | `tests/performance/k6/spike_test.js` |  |  |  |
| Soak test | `tests/performance/k6/soak_test.js` |  |  |  |

## 3) Metrics Summary
| Scenario | Avg Response Time (ms) | p95 Latency (ms) | Throughput (req/s) | Error Rate (%) |
|---|---:|---:|---:|---:|
| Read-heavy incidents |  |  |  |  |
| Write-heavy reports |  |  |  |  |
| Mixed workload |  |  |  |  |
| Spike test |  |  |  |  |
| Soak test |  |  |  |  |

## 4) Bottlenecks Identified
- **Bottleneck #1:**
  - Evidence:
  - Likely root cause:
  - Affected endpoints:
- **Bottleneck #2:**
  - Evidence:
  - Likely root cause:
  - Affected endpoints:

## 5) Optimizations Applied
| Optimization | Why | Expected impact | Status |
|---|---|---|---|
| Example: add DB index on incidents(status, reported_at) | slow filtered list query | lower p95 on read-heavy | done |

## 6) Before/After Comparison
| Metric | Before | After | Delta |
|---|---:|---:|---:|
| Avg response time (ms) |  |  |  |
| p95 latency (ms) |  |  |  |
| Throughput (req/s) |  |  |  |
| Error rate (%) |  |  |  |

## 7) Observed Limitations
- External API instability/timeout behavior:
- Data skew/uneven traffic patterns:
- Infrastructure constraints:

## 8) Next Optimization Iteration
1. 
2. 
3. 
