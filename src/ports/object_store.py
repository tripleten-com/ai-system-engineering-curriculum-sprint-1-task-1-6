"""Coldline — Task 1.1.

===================

File:              src/ports/object_store.py
Component:         Port — Object Store
Purpose:           Define the provider-neutral object-storage port.
Interacts With:    Use cases and provider adapters
Sprint/Task:       Sprint 1 — Project 1 / Task 1.1
Concepts:          Dependency inversion, provider-neutral interface
Tools:             Python 3.12
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ObjectStore(Protocol):
    """Read and write immutable evidence objects."""

    async def read(self, key: str) -> bytes:
        """Return the bytes stored under a provider-neutral key."""
        ...

    async def write(self, key: str, value: bytes) -> None:
        """Store bytes under a provider-neutral key."""
        ...
