from __future__ import annotations

from time import perf_counter

from prometheus_client import Counter, Histogram, make_wsgi_app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests.",
    ["method", "endpoint", "status_code"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "endpoint"],
)

bookings_created_total = Counter(
    "bookings_created_total", "Total number of bookings created."
)
bookings_cancelled_late_total = Counter(
    "bookings_cancelled_late_total", "Total number of late cancellations."
)
premium_validation_failures_total = Counter(
    "premium_validation_failures_total",
    "Total number of premium membership validation failures.",
)
ranked_validation_failures_total = Counter(
    "ranked_validation_failures_total",
    "Total number of ranked booking validation failures.",
)


def _endpoint_from_request(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and hasattr(route, "path"):
        return route.path
    return request.url.path


class MetricsMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware to capture request count and duration metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = perf_counter()
        endpoint = _endpoint_from_request(request)
        method = request.method
        status_code = "500"

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
            return response
        finally:
            duration = perf_counter() - start_time
            http_requests_total.labels(method, endpoint, status_code).inc()
            http_request_duration_seconds.labels(method, endpoint).observe(duration)


def get_metrics_app():
    """Return a WSGI app for Prometheus metrics scraping."""

    return make_wsgi_app()

