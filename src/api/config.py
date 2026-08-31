"""Coldline — Task 1.1.

===================

File:              src/api/config.py
Component:         API — Config
Purpose:           Own and validate every API environment read.
Interacts With:    FastAPI, domain, ports, and adapters
Sprint/Task:       Sprint 1 — Project 1 / Task 1.1
Concepts:          HTTP boundary, composition, asynchronous work
Tools:             Python 3.12, Redis, Pydantic
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    """Describe the protected runtime configuration for the API service."""

    model_config = SettingsConfigDict(env_prefix="COLDLINE_", extra="forbid")

    database_url: str = Field(min_length=1)
    redis_url: str = Field(min_length=1)
    otel_endpoint: str = Field(min_length=1)
    service_name: str = "coldline-api"
    stream_name: str = "coldline.exception.jobs"
    consumer_group: str = "coldline-workers"
