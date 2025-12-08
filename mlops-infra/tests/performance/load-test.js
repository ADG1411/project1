// k6 Performance Test for MLOps Infrastructure
import http from 'k6/http';
import encoding from 'k6/encoding';
import { check, group, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

// Test configuration
export const options = {
  stages: [
    { duration: '1m', target: 5 },   // Ramp up to 5 users over 1 minute
    { duration: '3m', target: 5 },   // Stay at 5 users for 3 minutes
    { duration: '1m', target: 10 },  // Ramp up to 10 users over 1 minute
    { duration: '3m', target: 10 },  // Stay at 10 users for 3 minutes
    { duration: '1m', target: 0 },   // Ramp down to 0 users over 1 minute
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2000'], // 95% of requests must complete below 2s
    'errors': ['rate<0.05'],             // Error rate must be below 5%
    'http_req_duration{group:::consul}': ['p(95)<1000'],
    'http_req_duration{group:::nomad}': ['p(95)<1000'], 
    'http_req_duration{group:::prometheus}': ['p(95)<2000'],
    'http_req_duration{group:::grafana}': ['p(95)<3000'],
  }
};

const BASE_URL = 'http://localhost';

// Service endpoints
const services = {
  consul: `${BASE_URL}:8500`,
  nomad: `${BASE_URL}:4646`,
  prometheus: `${BASE_URL}:9090`,
  grafana: `${BASE_URL}:3000`,
  pushgateway: `${BASE_URL}:9091`
};

export default function() {
  group('Consul API Tests', () => {
    // Health check
    let response = http.get(`${services.consul}/v1/status/leader`);
    check(response, {
      'consul leader status is 200': (r) => r.status === 200,
      'consul response time < 500ms': (r) => r.timings.duration < 500,
    });
    errorRate.add(response.status !== 200);
    responseTime.add(response.timings.duration);

    // Service catalog
    response = http.get(`${services.consul}/v1/catalog/services`);
    check(response, {
      'consul services catalog is 200': (r) => r.status === 200,
      'consul services response is JSON': (r) => r.headers['Content-Type'].includes('application/json'),
    });
    errorRate.add(response.status !== 200);

    // Key-value store test
    const testKey = `test-key-${Math.random().toString(36).substr(2, 9)}`;
    const testValue = `test-value-${Date.now()}`;
    
    // PUT operation
    response = http.put(`${services.consul}/v1/kv/${testKey}`, testValue);
    check(response, {
      'consul KV PUT is successful': (r) => r.status === 200,
    });

    // GET operation
    response = http.get(`${services.consul}/v1/kv/${testKey}`);
    check(response, {
      'consul KV GET is successful': (r) => r.status === 200,
    });

    // DELETE operation
    response = http.del(`${services.consul}/v1/kv/${testKey}`);
    check(response, {
      'consul KV DELETE is successful': (r) => r.status === 200,
    });
  });

  group('Nomad API Tests', () => {
    // Health check
    let response = http.get(`${services.nomad}/v1/status/leader`);
    check(response, {
      'nomad leader status is 200': (r) => r.status === 200,
      'nomad response time < 500ms': (r) => r.timings.duration < 500,
    });
    errorRate.add(response.status !== 200);
    responseTime.add(response.timings.duration);

    // Jobs list
    response = http.get(`${services.nomad}/v1/jobs`);
    check(response, {
      'nomad jobs list is 200': (r) => r.status === 200,
      'nomad jobs response is JSON': (r) => r.headers['Content-Type'].includes('application/json'),
    });
    errorRate.add(response.status !== 200);

    // Nodes list
    response = http.get(`${services.nomad}/v1/nodes`);
    check(response, {
      'nomad nodes list is 200': (r) => r.status === 200,
    });

    // Allocations
    response = http.get(`${services.nomad}/v1/allocations`);
    check(response, {
      'nomad allocations is 200': (r) => r.status === 200,
    });
  });

  group('Prometheus API Tests', () => {
    // Health check
    let response = http.get(`${services.prometheus}/-/healthy`);
    check(response, {
      'prometheus health is 200': (r) => r.status === 200,
      'prometheus response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    errorRate.add(response.status !== 200);
    responseTime.add(response.timings.duration);

    // Readiness check
    response = http.get(`${services.prometheus}/-/ready`);
    check(response, {
      'prometheus readiness is 200': (r) => r.status === 200,
    });

    // Query API - up metric
    response = http.get(`${services.prometheus}/api/v1/query?query=up`);
    check(response, {
      'prometheus query API is 200': (r) => r.status === 200,
      'prometheus query response is JSON': (r) => {
        try {
          const json = JSON.parse(r.body);
          return json.status === 'success';
        } catch (e) {
          return false;
        }
      },
    });
    errorRate.add(response.status !== 200);

    // Label values
    response = http.get(`${services.prometheus}/api/v1/label/__name__/values`);
    check(response, {
      'prometheus labels API is 200': (r) => r.status === 200,
    });

    // Targets
    response = http.get(`${services.prometheus}/api/v1/targets`);
    check(response, {
      'prometheus targets API is 200': (r) => r.status === 200,
    });
  });

  group('Grafana API Tests', () => {
    const auth = 'Basic ' + encoding.b64encode('admin:test-password-123');
    
    // Health check
    let response = http.get(`${services.grafana}/api/health`);
    check(response, {
      'grafana health is 200': (r) => r.status === 200,
      'grafana response time < 2000ms': (r) => r.timings.duration < 2000,
    });
    errorRate.add(response.status !== 200);
    responseTime.add(response.timings.duration);

    // Login check
    response = http.get(`${services.grafana}/login`, {
      headers: { 'Authorization': auth }
    });
    check(response, {
      'grafana login page accessible': (r) => r.status === 200,
    });

    // API datasources (authenticated)
    response = http.get(`${services.grafana}/api/datasources`, {
      headers: { 'Authorization': auth }
    });
    check(response, {
      'grafana datasources API accessible': (r) => r.status === 200,
    });

    // API dashboards (authenticated)  
    response = http.get(`${services.grafana}/api/search`, {
      headers: { 'Authorization': auth }
    });
    check(response, {
      'grafana search API accessible': (r) => r.status === 200,
    });
  });

  group('Pushgateway Tests', () => {
    // Health check
    let response = http.get(`${services.pushgateway}/-/healthy`);
    check(response, {
      'pushgateway health is 200': (r) => r.status === 200,
      'pushgateway response time < 500ms': (r) => r.timings.duration < 500,
    });
    errorRate.add(response.status !== 200);

    // Metrics endpoint
    response = http.get(`${services.pushgateway}/metrics`);
    check(response, {
      'pushgateway metrics is 200': (r) => r.status === 200,
      'pushgateway metrics contains prometheus format': (r) => r.body.includes('# HELP'),
    });

    // Push metric test
    const testMetric = `performance_test_metric{job="k6-test",instance="${__VU}-${__ITER}"} ${Math.random()}`;
    response = http.post(
      `${services.pushgateway}/metrics/job/k6-performance-test/instance/${__VU}-${__ITER}`,
      testMetric,
      {
        headers: { 'Content-Type': 'text/plain' }
      }
    );
    check(response, {
      'pushgateway metric push successful': (r) => r.status === 200 || r.status === 202,
    });
  });

  // Random sleep between 1-3 seconds
  sleep(Math.random() * 2 + 1);
}

export function handleSummary(data) {
  return {
    'performance-summary.json': JSON.stringify(data, null, 2),
    'stdout': createTextSummary(data),
  };
}

function createTextSummary(data) {
  const summary = [];
  
  summary.push('========== Performance Test Summary ==========');
  summary.push(`Test Duration: ${data.state.testRunDurationMs}ms`);
  summary.push(`Total Requests: ${data.metrics.http_reqs.values.count}`);
  summary.push(`Request Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)}/s`);
  summary.push(`Average Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms`);
  summary.push(`95th Percentile: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms`);
  summary.push(`Error Rate: ${(data.metrics.errors.values.rate * 100).toFixed(2)}%`);
  
  // Check if thresholds passed
  summary.push('\n========== Threshold Results ==========');
  for (const [name, threshold] of Object.entries(data.thresholds)) {
    const status = threshold.ok ? '✅ PASSED' : '❌ FAILED';
    summary.push(`${name}: ${status}`);
  }
  
  summary.push('\n========== Detailed Metrics ==========');
  
  // Group metrics
  for (const [groupName, groupData] of Object.entries(data.metrics)) {
    if (groupData.values) {
      summary.push(`\n${groupName}:`);
      for (const [key, value] of Object.entries(groupData.values)) {
        if (typeof value === 'number') {
          summary.push(`  ${key}: ${value.toFixed(2)}`);
        } else {
          summary.push(`  ${key}: ${value}`);
        }
      }
    }
  }
  
  return summary.join('\n') + '\n';
}