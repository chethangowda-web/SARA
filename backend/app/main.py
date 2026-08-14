from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="SARA — Smart Accountability & Resolution Assistant",
    description="AI-powered public grievance accountability layer API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set all CORS enabled origins
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

import logging
logging.basicConfig(level=logging.INFO)

from app.core.logging_middleware import LoggingMiddleware
app.add_middleware(LoggingMiddleware)

from app.core.security_headers_middleware import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

from app.api import auth, user_admin, grievances, governance, evidence, comments, notifications, dashboards, analytics

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(user_admin.router, prefix=settings.API_V1_STR)
app.include_router(grievances.router, prefix=settings.API_V1_STR)
app.include_router(governance.router, prefix=settings.API_V1_STR)
app.include_router(evidence.router, prefix=settings.API_V1_STR)
app.include_router(comments.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(dashboards.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router)

@app.get(f"{settings.API_V1_STR}/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

from fastapi import Request
from fastapi.responses import JSONResponse
import uuid

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger = logging.getLogger("sara_request_logger")
    logger.error(f"Unhandled Exception: request_id={request_id} detail={str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id
        },
        headers={"X-Request-ID": request_id}
    )
