"""Middleware for enhanced reliability and fault tolerance."""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Add request timeout handling."""

    def __init__(self, app, timeout: int = 30):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)

            if process_time > self.timeout * 0.8:  # Warn if close to timeout
                logger.warning(f"Request {request.url.path} took {process_time:.2f}s (close to timeout)")

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed after {process_time:.2f}s: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Request processing failed", "error": str(e)}
            )


class RetryMiddleware(BaseHTTPMiddleware):
    """Add automatic retry for transient failures."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        max_retries = 3
        retry_delay = 0.5

        for attempt in range(max_retries):
            try:
                response = await call_next(request)

                # Retry on 502, 503, 504 errors (gateway/service issues)
                if response.status_code in [502, 503, 504] and attempt < max_retries - 1:
                    logger.warning(f"Retrying request {request.url.path} (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue

                return response

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
                    return JSONResponse(
                        status_code=503,
                        content={"detail": "Service temporarily unavailable", "error": str(e)}
                    )

                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                time.sleep(retry_delay * (attempt + 1))

        return JSONResponse(status_code=503, content={"detail": "Max retries exceeded"})


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Simple circuit breaker to prevent cascading failures."""

    def __init__(self, app, failure_threshold: int = 5, timeout: int = 60):
        super().__init__(app)
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if circuit breaker is open
        if self.is_open:
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                # Try to close the circuit after timeout
                self.is_open = False
                self.failure_count = 0
                logger.info("Circuit breaker reset")
            else:
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Service temporarily unavailable (circuit open)"}
                )

        try:
            response = await call_next(request)

            if response.status_code >= 500:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.is_open = True
                    logger.error(f"Circuit breaker opened after {self.failure_count} failures")
            else:
                # Reset on success
                if self.failure_count > 0:
                    self.failure_count = max(0, self.failure_count - 1)

            return response

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                logger.error(f"Circuit breaker opened after exception: {e}")

            return JSONResponse(
                status_code=503,
                content={"detail": "Service error", "error": str(e)}
            )