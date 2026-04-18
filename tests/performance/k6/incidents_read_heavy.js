import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TOKEN = __ENV.ACCESS_TOKEN || '';

export const options = {
  vus: 30,
  duration: '3m',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.02'],
  },
};

export default function () {
  const params = {
    headers: TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {},
  };

  const res = http.get(
    `${BASE_URL}/api/v1/incidents/?page=1&page_size=20&sort_by=reported_at&order=desc&status=VERIFIED`,
    params
  );

  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(0.2);
}
