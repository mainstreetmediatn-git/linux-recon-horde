from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from .models import Agent, AgentState, MemoryRecord


@dataclass(slots=True)
class AuditEvent:
    event_type: str
    agent_id: str
    at: str
    details: dict[str, object] = field(default_factory=dict)


class LifecycleError(RuntimeError):
    pass


class LifecycleManager:
    """Constitution-governed lifecycle manager.

    This service manages admission, suspension, succession, retirement, and
    immutable audit history. It does not execute reconnaissance itself.
    """

    def __init__(self) -> None:
        self.agents: dict[str, Agent] = {}
        self.audit_log: list[AuditEvent] = []

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _record(self, event_type: str, agent_id: str, **details: object) -> None:
        self.audit_log.append(AuditEvent(event_type, agent_id, self._now(), details))

    def propose(self, agent: Agent) -> None:
        if agent.agent_id in self.agents:
            raise LifecycleError(f"agent already exists: {agent.agent_id}")
        agent.state = AgentState.PROPOSED
        self.agents[agent.agent_id] = agent
        self._record("agent.proposed", agent.agent_id, role=agent.role)

    def admit(self, agent_id: str, *, human_approved: bool) -> Agent:
        agent = self.agents[agent_id]
        if not human_approved:
            raise LifecycleError("human approval required for admission")
        if not agent.role or not agent.specialization:
            raise LifecycleError("role and specialization are required")
        if not agent.scopes:
            raise LifecycleError("at least one explicit scope is required")
        agent.state = AgentState.PROBATIONARY
        self._record("agent.admitted", agent_id)
        return agent

    def activate(self, agent_id: str, *, judge_approved: bool, auditor_approved: bool) -> Agent:
        agent = self.agents[agent_id]
        if agent.state not in {AgentState.PROBATIONARY, AgentState.SUCCESSOR_TRAINING}:
            raise LifecycleError("agent is not eligible for activation")
        if not (judge_approved and auditor_approved):
            raise LifecycleError("judge and auditor approval required")
        if agent.compliance_score < 0.95 or agent.health_score < 0.80:
            raise LifecycleError("agent does not meet readiness thresholds")
        agent.state = AgentState.ACTIVE
        self._record("agent.activated", agent_id)
        return agent

    def suspend(self, agent_id: str, reason: str) -> Agent:
        agent = self.agents[agent_id]
        agent.state = AgentState.SUSPENDED
        self._record("agent.suspended", agent_id, reason=reason)
        return agent

    def needs_successor(
        self,
        agent_id: str,
        *,
        max_tenure_cycles: int = 1000,
        min_health: float = 0.70,
        min_quality: float = 0.75,
    ) -> bool:
        agent = self.agents[agent_id]
        return (
            agent.tenure_cycles >= max_tenure_cycles
            or agent.health_score < min_health
            or (agent.evidence_quality > 0 and agent.evidence_quality < min_quality)
        )

    def create_successor(self, predecessor_id: str, successor: Agent) -> Agent:
        predecessor = self.agents[predecessor_id]
        if predecessor.successor_id:
            raise LifecycleError("predecessor already has a successor")
        successor.predecessor_id = predecessor_id
        successor.state = AgentState.SUCCESSOR_TRAINING
        successor.scopes = list(predecessor.scopes)
        successor.memory_namespaces = list(predecessor.memory_namespaces)
        successor.allowed_tools = list(predecessor.allowed_tools)
        self.agents[successor.agent_id] = successor
        predecessor.successor_id = successor.agent_id
        predecessor.state = AgentState.SUCCESSION_PENDING
        self._record("succession.started", predecessor_id, successor_id=successor.agent_id)
        self._record("successor.created", successor.agent_id, predecessor_id=predecessor_id)
        return successor

    def complete_handoff(
        self,
        predecessor_id: str,
        *,
        approved_memory: Iterable[MemoryRecord],
        judge_approved: bool,
        auditor_approved: bool,
        human_approved: bool,
    ) -> Agent:
        predecessor = self.agents[predecessor_id]
        if not predecessor.successor_id:
            raise LifecycleError("no successor exists")
        successor = self.agents[predecessor.successor_id]
        if successor.state is not AgentState.ACTIVE:
            raise LifecycleError("successor must be active before retirement")
        if not (judge_approved and auditor_approved and human_approved):
            raise LifecycleError("judge, auditor, and human approvals are required")

        transferable = [m.memory_id for m in approved_memory if m.state.value in {"active", "ratified"}]
        predecessor.state = AgentState.RETIREMENT_READY
        self._record(
            "succession.handoff",
            predecessor_id,
            successor_id=successor.agent_id,
            memory_ids=transferable,
        )
        predecessor.state = AgentState.RETIRED
        self._record("agent.retired", predecessor_id, successor_id=successor.agent_id)
        return predecessor

    def archive_retired(self, agent_id: str) -> Agent:
        agent = self.agents[agent_id]
        if agent.state is not AgentState.RETIRED:
            raise LifecycleError("only retired agents may be archived")
        agent.state = AgentState.ARCHIVED
        self._record("agent.archived", agent_id)
        return agent
