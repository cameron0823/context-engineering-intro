"""
Monitoring and error tracking configuration.
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from prometheus_client import Counter, Histogram, Gauge
import structlog
import time
from functools import wraps
from typing import Callable, Any

from src.core.config import settings

logger = structlog.get_logger()


# Prometheus metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)

db_query_count = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

external_api_calls = Counter(
    'external_api_calls_total',
    'External API calls',
    ['api', 'endpoint', 'status']
)

external_api_duration = Histogram(
    'external_api_duration_seconds',
    'External API call duration',
    ['api', 'endpoint']
)

business_metrics = Counter(
    'business_operations_total',
    'Business operations',
    ['operation', 'status']
)

estimate_values = Histogram(
    'estimate_values_dollars',
    'Estimate values in dollars',
    buckets=[100, 500, 1000, 2500, 5000, 10000, 25000, 50000]
)


def init_sentry():
    """Initialize Sentry error tracking."""
    if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint",
                    failed_request_status_codes={400, 403, 404, 405}
                ),
                SqlalchemyIntegration(),
                HttpxIntegration(),
                LoggingIntegration(
                    level=None,  # Capture all log levels
                    event_level=None  # Don't send logs as events
                )
            ],
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send personally identifiable information
            before_send=before_send_filter,
            release=f"{settings.APP_NAME}@{settings.APP_VERSION}"
        )
        logger.info("Sentry initialized", environment=settings.ENVIRONMENT)
    else:
        logger.info("Sentry DSN not configured, skipping initialization")


def before_send_filter(event, hint):
    """Filter sensitive data before sending to Sentry."""
    # Remove sensitive data from request
    if 'request' in event and 'data' in event['request']:
        data = event['request']['data']
        # Remove password fields
        for field in ['password', 'new_password', 'current_password', 'token', 'api_key']:
            if field in data:
                data[field] = '[FILTERED]'
    
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        for header in ['authorization', 'x-api-key', 'cookie']:
            if header in headers:
                headers[header] = '[FILTERED]'
    
    # Remove sensitive query parameters
    if 'request' in event and 'query_string' in event['request']:
        query = event['request']['query_string']
        for param in ['token', 'api_key', 'secret']:
            if param in query:
                query = query.replace(f"{param}=", f"{param}=[FILTERED]")
                event['request']['query_string'] = query
    
    return event


def track_request_metrics():
    """Decorator to track HTTP request metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            active_requests.inc()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                active_requests.dec()
                duration = time.time() - start_time
                
                # Extract request info from args
                request = None
                for arg in args:
                    if hasattr(arg, 'method') and hasattr(arg, 'url'):
                        request = arg
                        break
                
                if request:
                    endpoint = str(request.url.path)
                    method = request.method
                    status = getattr(result, 'status_code', 200) if 'result' in locals() else 500
                    
                    request_count.labels(
                        method=method,
                        endpoint=endpoint,
                        status=status
                    ).inc()
                    
                    request_duration.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(duration)
        
        return wrapper
    return decorator


def track_db_metrics(operation: str, table: str):
    """Decorator to track database query metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                db_query_count.labels(
                    operation=operation,
                    table=table
                ).inc()
                return result
            finally:
                duration = time.time() - start_time
                db_query_duration.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
        
        return wrapper
    return decorator


def track_external_api_call(api: str, endpoint: str):
    """Decorator to track external API calls."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                
                external_api_calls.labels(
                    api=api,
                    endpoint=endpoint,
                    status=status
                ).inc()
                
                external_api_duration.labels(
                    api=api,
                    endpoint=endpoint
                ).observe(duration)
        
        return wrapper
    return decorator


def track_business_operation(operation: str):
    """Decorator to track business operations."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                
                # Track estimate values if applicable
                if operation == "create_estimate" and hasattr(result, 'total_price'):
                    estimate_values.observe(float(result.total_price))
                
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                business_metrics.labels(
                    operation=operation,
                    status=status
                ).inc()
        
        return wrapper
    return decorator


class PerformanceMonitor:
    """Context manager for performance monitoring."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.logger = logger.bind(operation=operation_name)
    
    async def __aenter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting {self.operation_name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type:
            self.logger.error(
                f"{self.operation_name} failed",
                duration=duration,
                error=str(exc_val)
            )
            # Report error to Sentry
            sentry_sdk.capture_exception(exc_val)
        else:
            self.logger.info(
                f"{self.operation_name} completed",
                duration=duration
            )
        
        return False  # Don't suppress exceptions


# Custom health check endpoint data
health_check_results = Gauge(
    'health_check_status',
    'Health check status',
    ['component']
)


def update_health_status(component: str, healthy: bool):
    """Update health check status for monitoring."""
    health_check_results.labels(component=component).set(1 if healthy else 0)