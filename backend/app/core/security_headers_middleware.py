from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.core.config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Add standard security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Cache-Control for sensitive paths
        if request.url.path.startswith(("/api/v1/auth", "/api/v1/grievances", "/api/v1/analytics", "/api/v1/comments", "/api/v1/evidence")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            
        # HSTS in production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
        # Content Security Policy (strict default-src 'none' for API responses)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
        
        return response
