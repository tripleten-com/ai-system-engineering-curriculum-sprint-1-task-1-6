"""Coldline — Task 1.1.

===================

File:              src/adapters/persistence/__init__.py
Component:         Persistence adapters — Package exports
Purpose:           Expose internal persistence adapters.
Interacts With:    Domain contracts, ports, and local providers
Sprint/Task:       Sprint 1 — Project 1 / Task 1.1
Concepts:          Boundary translation, deterministic infrastructure
Tools:             Python 3.12
"""

from adapters.persistence.postgres import PostgresExceptionRepository

__all__ = ["PostgresExceptionRepository"]
