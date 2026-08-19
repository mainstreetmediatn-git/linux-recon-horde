from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from .models import Agent, Evidence, MissionContract
from .policy import ConstitutionPolicy, Decision


class JobState(str, Enum):
    QUEUED = "queued"
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
    state: JobState = JobState.QUEUED
    evidence_ids: list[str] = field(default_factory=list)
    error: str | None = None


class HordeOrchestrator:
    """Policy-gated coordinator for safe specialist jobs and evidence handoff."""

    def __init__(self, policy: ConstitutionPolicy | None = None) -> None:
        self.policy = policy or ConstitutionPolicy()

    def prepare_job(self, mission: MissionContract, agent: Agent, *, job_id: str, tool: str, target: str) -> AgentJob:
        mission_decision = self.policy.evaluate_mission(mission)
        if mission_decision.decision is not Decision.ALLOW:
            return AgentJob(job_id, mission.mission_id, agent.agent_id, tool, target, JobState.BLOCKED, error=mission_decision.reason)

        tool_decision = self.policy.evaluate_agent_tool_use(agent, tool=tool, target=target)
        if tool_decision.decision is not Decision.ALLOW:
            return AgentJob(job_id, mission.mission_id, agent.agent_id, tool, target, JobState.BLOCKED, error=tool_decision.reason)

        if agent.agent_id not in mission.participant_ids:
            return AgentJob(job_id, mission.mission_id, agent.agent_id, tool, target, JobState.BLOCKED, error="agent is not a mission participant")
        if tool not in mission.allowed_tools:
            return AgentJob(job_id, mission.mission_id, agent.agent_id, tool, target, JobState.BLOCKED, error="tool is not permitted by mission contract")
        if target not in mission.target_scope:
            return AgentJob(job_id, mission.mission_id, agent.agent_id, tool, target, JobState.BLOCKED, error="target is not permitted by mission contract")

        return AgentJob(job_id, mission.mission_id, agent.agent_id, tool, target)

    def run_evidence_job(self, job: AgentJob, operation: Callable[[], Evidence]) -> tuple[AgentJob, Evidence | None]:
        if job.state is JobState.BLOCKED:
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
