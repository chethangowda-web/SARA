import time
import uuid
import logging
import traceback
from datetime import datetime, timezone
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import decode_token

logger = logging.getLogger("sara_request_logger")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract user ID and role if authorization header is present
        user_id = None
        role = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_token(token)
                if payload.get("type") == "access":
                    user_id = payload.get("sub")
                    role = payload.get("role")
            except Exception:
                pass
        
        start_time = time.time()
        
        try:
            response: Response = await call_next(request)
            duration = round((time.time() - start_time) * 1000, 2)
            
            # Log structured request info
            logger.info(
                f"request_id={request_id} timestamp={datetime.now(timezone.utc).isoformat()} "
                f"method={request.method} path={request.url.path} status_code={response.status_code} "
                f"duration_ms={duration} user_id={user_id} role={role}"
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as exc:
            duration = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"request_id={request_id} timestamp={datetime.now(timezone.utc).isoformat()} "
                f"method={request.method} path={request.url.path} status_code=500 "
                f"duration_ms={duration} user_id={user_id} role={role} "
                f"exception={str(exc)}\n{traceback.format_exc()}"
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id
                },
                headers={"X-Request-ID": request_id}
            )
