import http from 'k6/http';
import { check, sleep } from 'k6';

// 100 concurrent virtual users testing SevaDristi API verification performance
export const options = {
  stages: [
    { duration: '30s', target: 20 },  // Ramp-up to 20 users
    { duration: '1m', target: 100 },  // Ramp-up to 100 users
    { duration: '2m', target: 100 },  // Sustained load at 100 concurrent users
    { duration: '30s', target: 0 },   // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<1500'], // 95% of requests should complete within 1.5s
    http_req_failed: ['rate<0.01'],    // Error rate must remain below 1%
  },
};

const BASE_URL = __ENV.API_URL || 'http://127.0.0.1:8000';

export default function () {
  // Test 1: Health check
  const healthRes = http.get(`${BASE_URL}/api/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
    'backend status is healthy': (r) => JSON.parse(r.body).status === 'healthy',
  });

  // Test 2: Verification endpoint with Synthetic Demo Preset (green)
  const payload = {
    scheme_id: 'ts_kalyana_lakshmi',
    preset_name: 'green',
    document_type: 'caste_certificate',
    applicant_data: {
      caste: 'BC-B',
      marital_status: 'unmarried',
      bride_age: 19
    }
  };

  const verifyRes = http.post(
    `${BASE_URL}/api/verify?preset_name=green&scheme_id=ts_kalyana_lakshmi`,
    JSON.stringify(payload),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  check(verifyRes, {
    'verify status is 200': (r) => r.status === 200,
    'has verification report': (r) => {
      const body = JSON.parse(r.body);
      return body && body.overall_status === 'READY';
    },
    'includes signed QR token': (r) => {
      const body = JSON.parse(r.body);
      return body && body.operator_token && body.operator_token.qr_signature;
    }
  });

  sleep(1);
}
