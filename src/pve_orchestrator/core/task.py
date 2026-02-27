"""Task model — what users submit to the orchestrator."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from .hardware import Capability


class TaskStatus(str, Enum):
    PENDING = "pending"
    ROUTING = "routing"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    LOW = 0
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class TaskConstraints(BaseModel):
    """Constraints on where/how the task can run."""

    max_latency_ms: Optional[int] = None
    preferred_node: Optional[str] = None
    excluded_nodes: list[str] = []
    min_vram_gb: Optional[float] = None
    require_warm_model: bool = False  # Only route to nodes with model already loaded


class Task(BaseModel):
    """A unit of work submitted to the orchestrator."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    type: Capability
    model: Optional[str] = None
    input: Any = None
    params: dict[str, Any] = {}

    priority: TaskPriority = TaskPriority.NORMAL
    constraints: TaskConstraints = TaskConstraints()

    # Lifecycle
    status: TaskStatus = TaskStatus.PENDING
    assigned_node: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Result
    result: Any = None
    error: Optional[str] = None

    @property
    def duration_ms(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None
