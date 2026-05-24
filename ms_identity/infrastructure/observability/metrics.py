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

membership_validations_total = Counter(
    "membership_validations_total", "Total number of membership validations."
)
restriction_checks_total = Counter(
    "restriction_checks_total", "Total number of restriction checks."
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

