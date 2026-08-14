import time
import uuid
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger("sara_rate_limiter")

class RateLimiter:
    def __init__(self, requests: int, window_seconds: int, scope: str = "ip"):
        """
        requests: max number of requests allowed in window_seconds
        window_seconds: duration of the rate limit window
        scope: "ip" or "user"
        """
        self.requests = requests
        self.window_seconds = window_seconds
        self.scope = scope
        self.redis_client = None
        try:
            self.redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception as e:
            logger.error(f"Failed to connect to Redis for rate limiting: {e}")

    async def __call__(self, request: Request):
        if not self.redis_client:
            return # Redis connection failed, bypass rate limiting
            
        # Get identifier based on scope
        identifier = None
        if self.scope == "user":
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                try:
                    from app.core.security import decode_token
                    payload = decode_token(token)
                    identifier = payload.get("sub")
                except Exception:
                    pass
            # Fallback to IP if not authenticated
            if not identifier:
                identifier = request.client.host if request.client else "unknown"
        else:
            identifier = request.client.host if request.client else "unknown"

        # Unique key for Redis
        key = f"rate_limit:{request.url.path}:{self.scope}:{identifier}"
        
        try:
            current_time = int(time.time())
            # Use redis transaction (pipeline)
            pipe = self.redis_client.pipeline()
            # Clear old records
            pipe.zremrangebyscore(key, 0, current_time - self.window_seconds)
            # Add current request unique member
            uniq_member = f"{current_time}:{uuid.uuid4()}"
            pipe.zadd(key, {uniq_member: current_time})
            # Get current count
            pipe.zcard(key)
            # Set expiry on key
            pipe.expire(key, self.window_seconds + 5)
            # Execute pipeline
            _, _, current_count, _ = await pipe.execute()
            
            if current_count > self.requests:
                # Get oldest remaining element to calculate Retry-After
                oldest = await self.redis_client.zrange(key, 0, 0, withscores=True)
                retry_after = self.window_seconds
                if oldest:
                    oldest_score = oldest[0][1]
                    retry_after = max(1, int(oldest_score + self.window_seconds - current_time))
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(retry_after)}
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Redis rate limiter exception (bypassing): {e}")
            return
