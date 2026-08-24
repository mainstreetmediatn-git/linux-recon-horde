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


class EnforcementMode(str, Enum):
    """How strongly Horde enforces the operator's own engagement policy."""

    ADVISORY = "advisory"
    ACKNOWLEDGE = "acknowledge"
    STRICT = "strict"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass(slots=True)
class OperatorPolicy:
    """Operator-owned rules of engagement.

    Horde reports metadata and applies only the controls configured here.
    It does not silently substitute a separate ruleset.
    """

    enforcement_mode: EnforcementMode = EnforcementMode.ADVISORY
    require_explicit_authorization: bool = False
    require_target_scope: bool = False
    require_tool_admission: bool = False
    require_module_admission: bool = False
    require_risk_acknowledgement: bool = False
    acknowledgement_at_or_above: RiskLevel = RiskLevel.HIGH
    allow_operator_override: bool = True
    audit_overrides: bool = True


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
    allowed_modules: list[str] = field(default_factory=list)
    operator_policy: OperatorPolicy = field(default_factory=OperatorPolicy)


@dataclass(slots=True)
class ExecutionRequest:
    """One operator-requested execution plan before any adapter runs."""

    request_id: str
    mission_id: str
    agent_id: str
    target: str
    module_id: str
    tool: str
    risk_level: RiskLevel = RiskLevel.LOW
    risk_acknowledged: bool = False
    operator_override: bool = False
    override_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
