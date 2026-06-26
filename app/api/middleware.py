import time
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("tides_api")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response: Response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Response-Time-Ms"] = f"{process_time:.2f}"
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = getattr(request.state, "request_id", "N/A")
        logger.info(f"Incoming request: {request.method} {request.url.path} | RequestID: {req_id}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code} for {request.method} {request.url.path} | RequestID: {req_id}")
        return response
