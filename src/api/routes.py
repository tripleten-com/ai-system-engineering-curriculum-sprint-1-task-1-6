"""Coldline.

===================

File:              src/api/routes.py
Component:         API — Routes
Purpose:           Expose the Coldline exception application through FastAPI.
Interacts With:    FastAPI, domain, ports, and adapters
Sprint/Task:       Sprint 1 — Project 1
Concepts:          HTTP boundary, composition, asynchronous work
Tools:             Python 3.12, FastAPI, OpenTelemetry, Prometheus, Pydantic
"""

from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import FastAPI, HTTPException, Request, Response, status
from opentelemetry import trace
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel
from starlette.types import Lifespan

from api.use_cases import (
    InRangeReading,
    QueueUnavailable,
    ReadingApplication,
    TerminalExceptionConflict,
)
from domain.contracts import ExceptionRecord, SensorReading
from domain.repositories import ExceptionRepository

_REQUESTS = Counter(
    "coldline_api_requests_total",
    "Count API requests by bounded route, method, and status.",
    ("route", "method", "status"),
)
_REQUEST_DURATION = Histogram(
    "coldline_api_request_duration_seconds",
    "Measure API request duration in seconds.",
    ("route", "method"),
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)


class AcceptedReading(BaseModel):
    """Return the stable identity and polling location for accepted work."""

    exception_id: str
    state: str
    status_url: str


async def _ready_by_default() -> bool:
    """Return readiness for dependency-free HTTP contract tests."""
    return True


def create_app(
    application: ReadingApplication,
    repository: ExceptionRepository,
    *,
    readiness: Callable[[], Awaitable[bool]] = _ready_by_default,
    lifespan: Lifespan[FastAPI] | None = None,
) -> FastAPI:
    """Create the HTTP delivery layer around provider-neutral application behavior."""
    app = FastAPI(title="Coldline API", version="1.1", lifespan=lifespan)

    @app.middleware("http")
    async def record_request(
        request: Request, call_next: Callable[..., Awaitable[Response]]
    ) -> Response:
        """Record bounded request count and duration labels."""
        started = perf_counter()
        route = _route_label(request.url.path)
        response_status = "500"
        try:
            response = await call_next(request)
            response_status = str(response.status_code)
            return response
        finally:
            # Unhandled server errors are re-raised by FastAPI. The finally block
            # still records their bounded 500 signal before error handling returns.
            _REQUESTS.labels(route, request.method, response_status).inc()
            _REQUEST_DURATION.labels(route, request.method).observe(perf_counter() - started)

    @app.get("/health/live", include_in_schema=False)
    async def liveness() -> dict[str, str]:
        """Report that the API process can serve requests."""
        return {"status": "alive"}

    @app.get("/health/ready", include_in_schema=False)
    async def ready(response: Response) -> dict[str, str]:
        """Report whether PostgreSQL and Redis are available to the API."""
        if not await readiness():
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "not_ready"}
        return {"status": "ready"}

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        """Expose Prometheus metrics for the API service."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post(
        "/api/v1/readings",
        response_model=AcceptedReading,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def accept_reading(reading: SensorReading) -> AcceptedReading:
        """Accept one synthetic exception reading for background processing."""
        try:
            record = await application.accept(reading)
        except InRangeReading as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except QueueUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except TerminalExceptionConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        trace.get_current_span().set_attribute("coldline.exception_id", record.exception_id)
        return AcceptedReading(
            exception_id=record.exception_id,
            state=record.state.value,
            status_url=f"/api/v1/exceptions/{record.exception_id}",
        )

    @app.get("/api/v1/exceptions/{exception_id}", response_model=ExceptionRecord)
    async def get_exception(exception_id: str) -> ExceptionRecord:
        """Return the durable state of one exception workflow."""
        record = await repository.get(exception_id)
        if record is None:
            raise HTTPException(status_code=404, detail="exception not found")
        return record

    return app


def _route_label(path: str) -> str:
    """Normalize request paths to bounded metric dimensions."""
    if path.startswith("/api/v1/exceptions/"):
        return "/api/v1/exceptions/{exception_id}"
    if path in {"/api/v1/readings", "/health/live", "/health/ready", "/metrics"}:
        return path
    return "unmatched"
