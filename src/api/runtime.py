"""Coldline.

===================

File:              src/api/runtime.py
Component:         API — Runtime
Purpose:           Expose initialized runtime adapters through provider-neutral collaborators.
Interacts With:    FastAPI, domain, ports, and adapters
Sprint/Task:       Sprint 1 — Project 1
Concepts:          HTTP boundary, composition, asynchronous work
Tools:             Python 3.12, PostgreSQL, Redis
"""

import asyncpg
from redis.asyncio import Redis

from domain.contracts import ExceptionJob, ExceptionRecord, ExceptionState, JobDelivery
from domain.repositories import ExceptionRepository
from ports import JobQueue


class RuntimeBindings:
    """Bridge FastAPI construction with adapters created during lifespan startup.

    FastAPI needs the application object before its asynchronous lifespan runs.
    This small forwarding object receives PostgreSQL and Redis adapters at
    startup and closes them through the composition root at shutdown.
    """

    def __init__(self) -> None:
        """Create an uninitialized binding set."""
        self.pool: asyncpg.Pool | None = None
        self.redis: Redis | None = None
        self.repository: ExceptionRepository | None = None
        self.queue: JobQueue | None = None

    async def get(self, exception_id: str) -> ExceptionRecord | None:
        """Forward one repository read after startup."""
        return await self._required_repository().get(exception_id)

    async def create(self, record: ExceptionRecord) -> ExceptionRecord:
        """Forward one repository create after startup."""
        return await self._required_repository().create(record)

    async def transition(
        self,
        exception_id: str,
        expected: set[ExceptionState],
        target: ExceptionState,
        *,
        summary: str | None = None,
        failure_reason: str | None = None,
    ) -> ExceptionRecord:
        """Forward one repository transition after startup."""
        return await self._required_repository().transition(
            exception_id,
            expected,
            target,
            summary=summary,
            failure_reason=failure_reason,
        )

    async def publish(self, job: ExceptionJob) -> str:
        """Forward one queue publication after startup."""
        if self.queue is None:
            raise RuntimeError("job queue is not initialized")
        return await self.queue.publish(job)

    async def read(self, *, block_ms: int = 1000) -> JobDelivery | None:
        """Forward a queue read when a consumer composition uses these bindings."""
        return await self._required_queue().read(block_ms=block_ms)

    async def claim_stale(self, *, minimum_idle_ms: int) -> JobDelivery | None:
        """Forward stale-delivery recovery when a consumer uses these bindings."""
        return await self._required_queue().claim_stale(minimum_idle_ms=minimum_idle_ms)

    async def acknowledge(self, message_id: str) -> None:
        """Forward one queue acknowledgement."""
        await self._required_queue().acknowledge(message_id)

    async def queue_depth(self) -> int:
        """Forward the queue-depth diagnostic."""
        return await self._required_queue().queue_depth()

    async def pending_count(self) -> int:
        """Forward the pending-delivery diagnostic."""
        return await self._required_queue().pending_count()

    async def ready(self) -> bool:
        """Return true only when both required API dependencies answer.

        Readiness is intentionally stricter than liveness. Any dependency error
        returns ``False`` so Compose and students receive a stable 503 response.
        """
        if self.pool is None or self.redis is None:
            return False
        try:
            database_ready = await self.pool.fetchval("SELECT 1") == 1
            redis_ready = bool(await self.redis.ping())
        except Exception:
            return False
        return database_ready and redis_ready

    def _required_repository(self) -> ExceptionRepository:
        """Return the initialized repository or fail with a startup defect."""
        if self.repository is None:
            raise RuntimeError("exception repository is not initialized")
        return self.repository

    def _required_queue(self) -> JobQueue:
        """Return the initialized job queue or fail with a startup defect."""
        if self.queue is None:
            raise RuntimeError("job queue is not initialized")
        return self.queue
