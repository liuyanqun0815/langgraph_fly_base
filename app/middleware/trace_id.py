import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from sale_app.util.traceId_log_handler import trace_id_var


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id_var.set(str(uuid.uuid4()).split("-")[-1])
        try:
            response = await call_next(request)
            return response
        finally:
            trace_id_var.set("N/A")
