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
  vus: 25,
  duration: '45m',
  thresholds: {
    http_req_duration: ['p(95)<800'],
    http_req_failed: ['rate<0.03'],
  },
};

export default function () {
  const selectedToken = tokenForCurrentVu();
  const readRes = http.get(`${BASE_URL}/api/v1/incidents/?page=1&page_size=20`, {
    headers: selectedToken ? { Authorization: `Bearer ${selectedToken}` } : {},
  });
  check(readRes, { 'read status 200': (r) => r.status === 200 });

  if (__ENV.SOAK_INCLUDE_WRITES === 'true' && __ITER % 120 === 0) {
    const payload = JSON.stringify({
      category_id: 2,
      checkpoint_id: null,
      description: `soak report ${Date.now()}`,
      latitude: 31.87,
      longitude: 35.24,
    });
    const writeRes = http.post(`${BASE_URL}/api/v1/reports/`, payload, {
      headers: {
        'Content-Type': 'application/json',
        ...(selectedToken ? { Authorization: `Bearer ${selectedToken}` } : {}),
      },
    });
    check(writeRes, { 'write status 200/201': (r) => [200, 201].includes(r.status) });
  }

  sleep(0.5);
}
