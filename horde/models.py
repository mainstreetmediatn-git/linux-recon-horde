from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentState(str, Enum):
    PROPOSED = "proposed"
    PROBATIONARY = "probationary"
    ACTIVE = "active"
    VETERAN = "veteran"
    SUCCESSION_PENDING = "succession_pending"
    SUCCESSOR_TRAINING = "successor_training"
    RETIREMENT_READY = "retirement_ready"
    RETIRED = "retired"
    SUSPENDED = "suspended"
    REMOVED = "removed"
    ARCHIVED = "archived"


class MemoryState(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CONTESTED = "contested"
    ARCHIVED = "archived"
    SEALED = "sealed"
    DRAFT = "draft"
    RATIFIED = "ratified"


@dataclass(slots=True)
class Evidence:
    evidence_id: str
    target: str
    source: str
    observed_at: str
    observation: str
    confidence: float
    agent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MemoryRecord:
    memory_id: str
    namespace: str
    title: str
    body: str
    author: str
    source: str
    confidence: float
    created_at: str
    state: MemoryState = MemoryState.ACTIVE
    evidence_ids: list[str] = field(default_factory=list)
    supersedes: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Agent:
    agent_id: str
    name: str
    role: str
    specialization: str
    state: AgentState = AgentState.PROPOSED
    trust_score: float = 0.5
    reputation_score: float = 0.5
    health_score: float = 1.0
    tenure_cycles: int = 0
    memory_namespaces: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    scopes: list[str] = field(default_factory=list)
    environment_id: str | None = None
    predecessor_id: str | None = None
    successor_id: str | None = None
    evidence_quality: float = 0.0
    compliance_score: float = 1.0
    mission_history: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MissionContract:
    mission_id: str
    objective: str
    target_scope: list[str]
    success_criteria: list[str]
    constraints: list[str]
    participant_ids: list[str]
    required_evidence: list[str]
    allowed_tools: list[str]
    approval_gates: list[str]
    report_requirements: list[str]
    authorized: bool = False
