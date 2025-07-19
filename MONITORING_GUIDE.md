# Monitoring and Observability Guide

This guide covers the monitoring and observability features implemented in the Cox Tree Service Estimating Application.

## Overview

The application includes comprehensive monitoring through:
- **Prometheus Metrics**: Performance and business metrics
- **Sentry Error Tracking**: Real-time error monitoring and alerting
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Health Checks**: Detailed health status endpoint

## Prometheus Metrics

### Available Metrics

#### HTTP Metrics
- `http_requests_total`: Total HTTP requests by method, endpoint, and status
- `http_request_duration_seconds`: Request duration histogram
- `http_requests_active`: Currently active requests

#### Database Metrics
- `db_queries_total`: Total database queries by operation and table
- `db_query_duration_seconds`: Query execution time

#### External API Metrics
- `external_api_calls_total`: External API calls by service and status
- `external_api_duration_seconds`: API call duration

#### Business Metrics
- `business_operations_total`: Business operations (create estimate, approve, etc.)
- `estimate_values_dollars`: Histogram of estimate values

#### Health Check Metrics
- `health_check_status`: Component health status (1=healthy, 0=unhealthy)

### Accessing Metrics

Prometheus metrics are available at: `http://localhost:8000/metrics`

### Example Prometheus Queries

```promql
# Request rate per minute
rate(http_requests_total[1m])

# Average request duration by endpoint
http_request_duration_seconds_sum / http_request_duration_seconds_count

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# External API success rate
rate(external_api_calls_total{status="success"}[5m]) / rate(external_api_calls_total[5m])

# Average estimate value
estimate_values_dollars_sum / estimate_values_dollars_count
```

## Sentry Error Tracking

### Configuration

Set the `SENTRY_DSN` environment variable:
```bash
SENTRY_DSN=https://your-key@sentry.io/project-id
```

### Features

- Automatic error capture with stack traces
- User context tracking (without PII)
- Performance monitoring
- Release tracking
- Environment separation (dev/staging/prod)

### Sensitive Data Filtering

The following data is automatically filtered:
- Passwords and tokens
- API keys
- Authorization headers
- Cookie values

## Structured Logging

### Log Format

All logs use structured JSON format:
```json
{
  "timestamp": "2024-07-19T10:30:45.123Z",
  "level": "info",
  "logger": "src.api.estimates",
  "request_id": "uuid-here",
  "message": "Estimate created",
  "estimate_id": 123,
  "duration": 0.234
}
```

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical failures

### Request Correlation

Every request gets a unique ID accessible via:
- Response header: `X-Request-ID`
- Log field: `request_id`

## Health Check Endpoint

### Endpoint: `/health`

Returns comprehensive health status:
```json
{
  "status": "healthy|degraded|unhealthy",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": 1234567890,
  "checks": {
    "cache": {
      "status": "healthy"
    },
    "external_apis": {
      "google_maps": {"status": "healthy"},
      "quickbooks": {"status": "unhealthy", "error": "..."},
      "fuel_api": {"status": "healthy"},
      "overall": "degraded"
    }
  }
}
```

### Health Check Monitoring

Use the health endpoint for:
- Load balancer health checks
- Uptime monitoring (Pingdom, UptimeRobot)
- Kubernetes liveness/readiness probes

## Performance Monitoring

### Request Tracking

Every response includes:
- `X-Request-ID`: Unique request identifier
- `X-Response-Time`: Request duration in seconds

### Performance Patterns

Use the `PerformanceMonitor` context manager:
```python
async with PerformanceMonitor("complex_operation"):
    # Your code here
    pass
```

### Decorators

Track specific operations:
```python
@track_business_operation("create_estimate")
async def create_estimate(...):
    pass

@track_external_api_call("google_maps", "distance_matrix")
async def calculate_distance(...):
    pass
```

## Alerting Rules (Prometheus)

Example alert rules for `prometheus/alerts.yml`:

```yaml
groups:
  - name: app_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowRequests
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2
        for: 5m
        annotations:
          summary: "95th percentile response time > 2s"
          
      - alert: ExternalAPIDown
        expr: health_check_status{component=~"api_.*"} == 0
        for: 10m
        annotations:
          summary: "External API unhealthy"
```

## Dashboard Setup

### Grafana Dashboard

Import the provided Grafana dashboard JSON or create one with:

1. **Overview Panel**: Request rate, error rate, response time
2. **Business Metrics**: Estimates created, approval rate, average values
3. **External APIs**: Success rates, response times
4. **System Health**: Component status, resource usage

### Key Metrics to Monitor

1. **Golden Signals**:
   - Latency: Response time percentiles
   - Traffic: Requests per second
   - Errors: Error rate
   - Saturation: Active requests, queue depth

2. **Business KPIs**:
   - Estimates created per day
   - Average estimate value
   - Approval rate
   - Time to approval

3. **External Dependencies**:
   - API availability
   - API response times
   - Rate limit usage

## Troubleshooting

### Common Issues

1. **Metrics not appearing**: Check if Prometheus is scraping the `/metrics` endpoint
2. **Sentry not receiving errors**: Verify `SENTRY_DSN` is set correctly
3. **Missing request IDs**: Ensure middleware is properly configured
4. **Health check timeouts**: External API checks may be slow, consider caching

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

## Best Practices

1. **Use correlation IDs**: Always include request_id in log messages
2. **Add business context**: Log business-relevant data (estimate_id, user_id)
3. **Monitor trends**: Look for patterns, not just thresholds
4. **Set up alerts**: Proactive monitoring prevents outages
5. **Regular reviews**: Review metrics and adjust alerts monthly

## Integration Examples

### CloudWatch Integration

```python
# Send custom metrics to CloudWatch
import boto3
cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='TreeService',
    MetricData=[{
        'MetricName': 'EstimateValue',
        'Value': float(estimate.total_price),
        'Unit': 'None'
    }]
)
```

### Datadog Integration

Use the Datadog Prometheus integration or install the Datadog agent with:
```yaml
# datadog.yaml
logs_enabled: true
apm_enabled: true
process_config:
  enabled: true
```

## Security Considerations

- Never log sensitive data (passwords, tokens, PII)
- Use Sentry's data scrubbing features
- Restrict access to metrics and logs
- Rotate log files regularly
- Encrypt logs in transit and at rest