import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("riskpilot")


def register_middleware(app):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled error on %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=500,
                content={"detail": "Something went wrong on the server. Please try again."},
            )
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s status=%s time=%.0fms role=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request.headers.get("x-role", "-"),
        )
        return response