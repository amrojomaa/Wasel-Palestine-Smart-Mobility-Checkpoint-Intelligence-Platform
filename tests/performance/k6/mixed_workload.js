import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TOKEN = __ENV.ACCESS_TOKEN || '';
const TOKEN_POOL = (__ENV.ACCESS_TOKENS || '')
  .split(',')
  .map((token) => token.trim())
  .filter((token) => token.length > 0);

function tokenForCurrentVu() {
  if (TOKEN_POOL.length > 0) {
    const index = (exec.vu.idInTest - 1) % TOKEN_POOL.length;
    return TOKEN_POOL[index];
  }
  return TOKEN;
}

export const options = {
  scenarios: {
    reads: {
      executor: 'constant-vus',
      vus: 20,
      duration: '4m',
      exec: 'readScenario',
    },
    writes: {
      executor: 'constant-vus',
      vus: 4,
      duration: '4m',
      exec: 'writeScenario',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<650'],
    http_req_failed: ['rate<0.03'],
  },
};

export function readScenario() {
  const selectedToken = tokenForCurrentVu();
  const headers = {
    'Content-Type': 'application/json',
    ...(selectedToken ? { Authorization: `Bearer ${selectedToken}` } : {}),
  };
  const res = http.get(`${BASE_URL}/api/v1/incidents/?page=1&page_size=10`, { headers });
  check(res, { 'read status 200': (r) => r.status === 200 });
  sleep(0.2);
}

export function writeScenario() {
  const selectedToken = tokenForCurrentVu();
  const headers = {
    'Content-Type': 'application/json',
    ...(selectedToken ? { Authorization: `Bearer ${selectedToken}` } : {}),
  };
  const payload = JSON.stringify({
    category_id: 3,
    checkpoint_id: null,
    description: `mixed write ${Date.now()}`,
    latitude: 31.88,
    longitude: 35.2,
  });
  const res = http.post(`${BASE_URL}/api/v1/reports/`, payload, { headers });
  check(res, { 'write status 200/201': (r) => [200, 201].includes(r.status) });
  // Keep write pressure under anti-abuse thresholds while reads stay concurrent.
  sleep(11);
}
