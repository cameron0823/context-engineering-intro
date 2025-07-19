"""
Main FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import structlog
import time
import uuid

from src.core.config import settings
from src.api import auth, estimates, costs, external
from src.core.cache import init_cache, close_cache
from src.core.rate_limit import limiter, rate_limit_exceeded_handler
from src.core.monitoring import init_sentry, track_request_metrics, PerformanceMonitor
# Future imports - will be added as we create them
# from src.api import reports
# from src.db.session import init_db


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    """
    # Startup
    logger.info("Starting Tree Service Estimating Application", 
                version=settings.APP_VERSION,
                environment=settings.ENVIRONMENT)
    
    # Initialize monitoring
    init_sentry()
    logger.info("Monitoring initialized")
    
    # Initialize database
    # await init_db()
    
    # Initialize cache
    await init_cache()
    logger.info("Cache initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Close database connections
    # await close_db()
    
    # Close cache connections
    await close_cache()
    logger.info("Cache closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Configure CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add monitoring middleware
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """Add monitoring and tracking to all requests."""
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Start timing
    start_time = time.time()
    
    # Add request ID to logger context
    with structlog.contextvars.bind_contextvars(request_id=request_id):
        try:
            response = await call_next(request)
            
            # Log request
            duration = time.time() - start_time
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration
            )
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration=duration,
                error=str(e)
            )
            raise

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(estimates.router, prefix="/api/estimates", tags=["Estimates"])
app.include_router(costs.router, prefix="/api/costs", tags=["Costs"])
app.include_router(external.router, prefix="/api/external", tags=["External APIs"])
# Future routers - will be added as we create them
# app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    from src.services.external_apis import ExternalAPIService
    from src.core.monitoring import update_health_status
    
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Check cache
    try:
        from src.core.cache import get_cache
        cache = get_cache()
        if cache:
            await cache.ping()
            health_status["checks"]["cache"] = {"status": "healthy"}
            update_health_status("cache", True)
        else:
            health_status["checks"]["cache"] = {"status": "unavailable"}
            update_health_status("cache", False)
    except Exception as e:
        health_status["checks"]["cache"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
        update_health_status("cache", False)
    
    # Check external APIs
    try:
        async with ExternalAPIService() as api_service:
            api_health = await api_service.get_api_health_status()
            health_status["checks"]["external_apis"] = api_health
            
            # Update individual API health metrics
            for api_name, api_status in api_health.items():
                if api_name != "overall":
                    is_healthy = api_status.get("status") == "healthy"
                    update_health_status(f"api_{api_name}", is_healthy)
                    
            if api_health.get("overall") != "healthy":
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["external_apis"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"
    
    # TODO: Add database health check when implemented
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )