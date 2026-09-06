"""Coldline.

===================

File:              src/domain/contracts.py
Component:         Domain — Contracts
Purpose:           Define provider-neutral contracts for exception processing.
Interacts With:    API and worker use cases
Sprint/Task:       Sprint 1 — Project 1
Concepts:          Business rules, immutable contracts, state
Tools:             Python 3.12, Pydantic
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExceptionState(StrEnum):
    """Describe the observable lifecycle of one exception."""

    RECEIVED = "RECEIVED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SensorReading(BaseModel):
    """Represent one synthetic shipment sensor observation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reading_id: str = Field(min_length=1, max_length=80)
    shipment_id: str = Field(min_length=1, max_length=80)
    temperature_c: float
    allowed_min_c: float
    allowed_max_c: float
    recorded_at: datetime
    context: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def validate_range(self) -> "SensorReading":
        """Reject a handling range whose minimum is not below its maximum."""
        if self.allowed_min_c >= self.allowed_max_c:
            raise ValueError("allowed_min_c must be below allowed_max_c")
        return self


class ExceptionJob(BaseModel):
    """Carry one validated exception across the queue boundary."""

    model_config = ConfigDict(frozen=True)

    exception_id: str
    reading: SensorReading
    accepted_at: datetime


class JobDelivery(BaseModel):
    """Describe one provider-neutral queue delivery attempt."""

    model_config = ConfigDict(frozen=True)

    message_id: str
    job: ExceptionJob
    delivery_count: int = Field(ge=1)
    trace_carrier: dict[str, str] = Field(default_factory=dict)


class ModelRequest(BaseModel):
    """Describe the provider-neutral input for an exception summary."""

    model_config = ConfigDict(frozen=True)

    exception_id: str
    shipment_id: str
    temperature_c: float
    allowed_min_c: float
    allowed_max_c: float


class ModelSummary(BaseModel):
    """Describe the deterministic provider response stored by Coldline."""

    model_config = ConfigDict(frozen=True)

    summary: str
    provider: str


class ExceptionRecord(BaseModel):
    """Represent the durable state of one exception workflow."""

    model_config = ConfigDict(frozen=True)

    exception_id: str
    reading: SensorReading
    state: ExceptionState
    accepted_at: datetime
    updated_at: datetime
    summary: str | None = None
    failure_reason: str | None = None
