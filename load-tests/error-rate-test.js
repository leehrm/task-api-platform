import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || '6m',
  thresholds: {
    http_req_failed: ['rate>0.05'],
  },
};

const BASE_URL = __ENV.BASE_URL;

export default function () {
  const res = http.get(`${BASE_URL}/debug/error`);

  check(res, {
    'debug error status is 500': (r) => r.status === 500,
  });

  sleep(1);
}
