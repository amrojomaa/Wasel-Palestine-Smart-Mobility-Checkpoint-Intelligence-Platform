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
  vus: 4,
  duration: '3m',
  thresholds: {
    http_req_duration: ['p(95)<700'],
    http_req_failed: ['rate<0.03'],
  },
};

export default function () {
  const selectedToken = tokenForCurrentVu();
  const payload = JSON.stringify({
    category_id: 2,
    checkpoint_id: null,
    latitude: 31.85,
    longitude: 35.21,
    description: `k6 write-heavy report at ${new Date().toISOString()}`,
    source_channel: 'MOBILE',
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      ...(selectedToken ? { Authorization: `Bearer ${selectedToken}` } : {}),
    },
  };

  const res = http.post(`${BASE_URL}/api/v1/reports/`, payload, params);

  check(res, {
    'status is 201 or 200': (r) => r.status === 201 || r.status === 200,
  });

  // Keep user-level writes under cooldown thresholds to avoid synthetic 429s.
  sleep(11);
}
