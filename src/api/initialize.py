"""Coldline.

===================

File:              src/api/initialize.py
Component:         Initialization composition root
Purpose:           Wire clients and initialize the database schema and Redis consumer group.
Interacts With:    FastAPI, domain, ports, and adapters
Sprint/Task:       Sprint 1 — Project 1
Concepts:          HTTP boundary, composition, asynchronous work
Tools:             Python 3.12, PostgreSQL, Redis
"""

import asyncio
from pathlib import Path

import asyncpg
from redis.asyncio import Redis

from adapters.queue import RedisJobQueue
from api.config import ApiSettings


async def initialize() -> None:
    """Wire infrastructure clients and apply idempotent initialization.

    This one-shot process is a composition root. It may construct provider
    clients, but it delegates queue behavior to the supplied adapter.
    """
    settings = ApiSettings()  # type: ignore[call-arg]  # values come from the protected environment
    schema_path = Path("infra/postgres/001_opening_checkpoint.sql")
    schema = schema_path.read_text(encoding="utf-8")
    connection = await asyncpg.connect(dsn=settings.database_url)
    redis = Redis.from_url(settings.redis_url)
    try:
        await connection.execute(schema)
        queue = RedisJobQueue(
            redis,
            stream=settings.stream_name,
            group=settings.consumer_group,
            consumer="initializer",
        )
        await queue.initialize()
    finally:
        await redis.aclose()
        await connection.close()


if __name__ == "__main__":
    asyncio.run(initialize())
