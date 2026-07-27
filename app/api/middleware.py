import uuid
from collections.abc import Awaitable, Callable

import jwt
from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.logging import request_id_ctx_var

# --- Rate Limiter ---
# Module-level singleton. Key = client IP. Default limit from config.
# Health endpoints are exempt via EXEMPT_PATHS below.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_default],
    headers_enabled=False,
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


EXEMPT_PATHS = {"/v1/health", "/v1/health/ready"}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401, content={"error": "Missing or invalid Authorization header"}
            )

        token = auth_header.removeprefix("Bearer ")
        try:
            jwt.decode(token, settings.jwt_signing_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"error": "Token has expired"})
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"error": "Invalid token"})

        return await call_next(request)
