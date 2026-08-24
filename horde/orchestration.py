from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from .models import Agent, Evidence, ExecutionRequest, MissionContract
from .policy import ConstitutionPolicy, Decision, PolicyDecision


class JobState(str, Enum):
    QUEUED = "queued"
    NEEDS_ACKNOWLEDGEMENT = "needs_acknowledgement"
    BLOCKED = "blocked"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass(slots=True)
class AgentJob:
    job_id: str
    mission_id: str
    agent_id: str
    tool: str
    target: str
    module_id: str = ""
    state: JobState = JobState.QUEUED
    evidence_ids: list[str] = field(default_factory=list)
    error: str | None = None
    policy_decision: str = Decision.ALLOW.value
    policy_reason: str = ""
    policy_warnings: list[str] = field(default_factory=list)
    override_applied: bool = False
    override_reason: str | None = None


class HordeOrchestrator:
    """Operator-policy coordinator for specialist jobs and evidence handoff.

    The orchestrator does not invent its own rules of engagement. It evaluates
    each request against the OperatorPolicy attached to the mission, preserves
    warnings and override state, and exposes the resulting execution state.
    """

    def __init__(self, policy: ConstitutionPolicy | None = None) -> None:
        self.policy = policy or ConstitutionPolicy()

    @staticmethod
    def _job_from_decision(request: ExecutionRequest, decision: PolicyDecision) -> AgentJob:
        if decision.decision is Decision.DENY:
            state = JobState.BLOCKED
        elif decision.decision is Decision.REQUIRE_ACKNOWLEDGEMENT:
            state = JobState.NEEDS_ACKNOWLEDGEMENT
        else:
            # ALLOW and WARN both remain runnable. WARN is advisory metadata.
            state = JobState.QUEUED

        return AgentJob(
            job_id=request.request_id,
            mission_id=request.mission_id,
            agent_id=request.agent_id,
            tool=request.tool,
            target=request.target,
            module_id=request.module_id,
            state=state,
            error=decision.reason if state is JobState.BLOCKED else None,
            policy_decision=decision.decision.value,
            policy_reason=decision.reason,
            policy_warnings=list(decision.warnings),
            override_applied=decision.override_applied,
            override_reason=request.override_reason if decision.override_applied else None,
        )

    def prepare_request(self, mission: MissionContract, agent: Agent, request: ExecutionRequest) -> AgentJob:
        if request.mission_id != mission.mission_id:
            return AgentJob(
                request.request_id,
                request.mission_id,
                request.agent_id,
                request.tool,
                request.target,
                request.module_id,
                state=JobState.BLOCKED,
                error="request mission_id does not match supplied mission",
                policy_decision=Decision.DENY.value,
                policy_reason="request/mission identity mismatch",
            )
        if request.agent_id != agent.agent_id:
            return AgentJob(
                request.request_id,
                request.mission_id,
                request.agent_id,
                request.tool,
                request.target,
                request.module_id,
                state=JobState.BLOCKED,
                error="request agent_id does not match supplied agent",
                policy_decision=Decision.DENY.value,
                policy_reason="request/agent identity mismatch",
            )

        decision = self.policy.evaluate_request(mission, agent, request)
        return self._job_from_decision(request, decision)

    def prepare_job(
        self,
        mission: MissionContract,
        agent: Agent,
        *,
        job_id: str,
        tool: str,
        target: str,
        module_id: str = "legacy",
    ) -> AgentJob:
        """Backward-compatible adapter using the mission's operator policy."""
        request = ExecutionRequest(
            request_id=job_id,
            mission_id=mission.mission_id,
            agent_id=agent.agent_id,
            target=target,
            module_id=module_id,
            tool=tool,
        )
        return self.prepare_request(mission, agent, request)

    def acknowledge_job(self, job: AgentJob) -> AgentJob:
        """Operator acknowledgement advances a waiting job without rewriting its audit context."""
        if job.state is JobState.NEEDS_ACKNOWLEDGEMENT:
            job.state = JobState.QUEUED
            job.policy_decision = Decision.ALLOW.value
            job.policy_reason = "operator acknowledgement recorded"
        return job

    def run_evidence_job(self, job: AgentJob, operation: Callable[[], Evidence]) -> tuple[AgentJob, Evidence | None]:
        if job.state in {JobState.BLOCKED, JobState.NEEDS_ACKNOWLEDGEMENT}:
            return job, None
        job.state = JobState.RUNNING
        try:
            evidence = operation()
        except Exception as exc:
            job.state = JobState.FAILED
            job.error = str(exc)
            return job, None
        job.evidence_ids.append(evidence.evidence_id)
        job.state = JobState.COMPLETE
        return job, evidence
