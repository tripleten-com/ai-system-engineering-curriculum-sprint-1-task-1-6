"""Coldline.

===================

File:              src/api/bootstrap.py
Component:         API — Bootstrap
Purpose:           Compose and run the Coldline API service.
Interacts With:    FastAPI, domain, ports, and adapters
Sprint/Task:       Sprint 1 — Project 1
Concepts:          HTTP boundary, composition, asynchronous work
Tools:             Python 3.12, FastAPI, PostgreSQL, Redis, OpenTelemetry
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import asyncpg
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from redis.asyncio import Redis

from adapters.logging import configure_json_logging
from adapters.persistence import PostgresExceptionRepository
from adapters.queue import RedisJobQueue
from adapters.telemetry import configure_tracing
from api.config import ApiSettings
from api.routes import create_app
from api.runtime import RuntimeBindings
from api.use_cases import ReadingApplication

settings = ApiSettings()  # type: ignore[call-arg]  # values come from the protected environment
configure_json_logging(settings.service_name)
tracer_provider = configure_tracing(settings.service_name, settings.otel_endpoint)
RedisInstrumentor().instrument()
bindings = RuntimeBindings()
application = ReadingApplication(bindings, bindings, clock=lambda: datetime.now(UTC))


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Own API dependency startup and shutdown.

    PostgreSQL and Redis clients are created once per process. The ``finally``
    block closes both clients and flushes tracing even when startup work or a
    request fails.
    """
    bindings.pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=4)
    bindings.redis = Redis.from_url(settings.redis_url)
    bindings.repository = PostgresExceptionRepository(bindings.pool)
    bindings.queue = RedisJobQueue(
        bindings.redis,
        stream=settings.stream_name,
        group=settings.consumer_group,
        consumer="api-publisher",
    )
    try:
        yield
    finally:
        await bindings.redis.aclose()
        await bindings.pool.close()
        tracer_provider.shutdown()


app = create_app(application, bindings, readiness=bindings.ready, lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
