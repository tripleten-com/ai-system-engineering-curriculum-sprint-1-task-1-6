"""Coldline.

===================

File:              src/ports/retriever.py
Component:         Port — Retriever
Purpose:           Define the provider-neutral retrieval port.
Interacts With:    Use cases and provider adapters
Sprint/Task:       Sprint 1 — Project 1
Concepts:          Dependency inversion, provider-neutral interface
Tools:             Python 3.12
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Retriever(Protocol):
    """Retrieve bounded procedure records."""

    async def search(self, query: str) -> list[str]:
        """Return relevant procedure records for a query."""
        ...
