"""
Rate limiting configuration for API endpoints.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()


# Custom key function that considers both IP and user ID for authenticated requests
def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key based on IP address and optionally user ID.
    
    For authenticated requests, uses combination of IP and user ID.
    For anonymous requests, uses only IP address.
    """
    # Get IP address
    ip = get_remote_address(request)
    
    # Try to get user ID from request state (set by auth middleware)
    user_id = getattr(request.state, 'user_id', None)
    
    if user_id:
        return f"{ip}:{user_id}"
    return ip


# Create limiter instance
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["200 per hour"],  # Global default limit
    headers_enabled=True,  # Return rate limit info in headers
    storage_uri=None,  # Use in-memory storage (can be configured for Redis)
)


# Custom error handler for rate limit exceeded
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom error response for rate limit exceeded.
    """
    response = JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}",
            "error": "rate_limit_exceeded",
            "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else None
        }
    )
    
    # Log rate limit violation
    logger.warning(
        "rate_limit_exceeded",
        ip=get_remote_address(request),
        path=request.url.path,
        limit=str(exc.limit),
        user_id=getattr(request.state, 'user_id', None)
    )
    
    # Add rate limit headers
    response.headers["Retry-After"] = str(exc.retry_after) if hasattr(exc, 'retry_after') else "60"
    response.headers["X-RateLimit-Limit"] = str(exc.limit.amount)
    response.headers["X-RateLimit-Remaining"] = "0"
    response.headers["X-RateLimit-Reset"] = str(exc.reset_time) if hasattr(exc, 'reset_time') else ""
    
    return response


# Rate limit decorators for different endpoint types
class RateLimits:
    """Common rate limits for different endpoint types."""
    
    # Authentication endpoints - strict limits to prevent brute force
    auth_login = "5 per minute"
    auth_register = "3 per hour"
    auth_password_reset = "3 per hour"
    
    # API endpoints - more generous limits
    api_read = "100 per minute"
    api_write = "30 per minute"
    api_delete = "10 per minute"
    
    # External API proxies - based on upstream limits
    google_maps = "50 per hour"  # Stay well under daily limit
    quickbooks = "100 per hour"
    fuel_api = "20 per hour"
    
    # File uploads
    file_upload = "10 per hour"
    
    # Reports and exports
    report_generation = "5 per hour"