from horde.models import (
    Agent,
    EnforcementMode,
    Evidence,
    ExecutionRequest,
    MissionContract,
    OperatorPolicy,
    RiskLevel,
)
from horde.orchestration import HordeOrchestrator, JobState


def mission(policy: OperatorPolicy) -> MissionContract:
    return MissionContract(
        mission_id="m1",
        objective="Operator-controlled execution",
        target_scope=["lab.local"],
        success_criteria=[],
        constraints=[],
        participant_ids=["a1"],
        required_evidence=[],
        allowed_tools=["tool-a"],
        approval_gates=[],
        report_requirements=[],
        authorized=True,
        allowed_modules=["mod-a"],
        operator_policy=policy,
    )


def agent() -> Agent:
    return Agent(
        agent_id="a1",
        name="Agent One",
        role="specialist",
        specialization="general",
        scopes=["lab.local"],
        allowed_tools=["tool-a"],
    )


def request(**overrides) -> ExecutionRequest:
    values = dict(
        request_id="req-1",
        mission_id="m1",
        agent_id="a1",
        target="lab.local",
        module_id="mod-a",
        tool="tool-a",
        risk_level=RiskLevel.LOW,
    )
    values.update(overrides)
    return ExecutionRequest(**values)


def test_advisory_findings_remain_runnable():
    policy = OperatorPolicy(
        enforcement_mode=EnforcementMode.ADVISORY,
        require_target_scope=True,
    )
    job = HordeOrchestrator().prepare_request(
        mission(policy),
        agent(),
        request(target="operator-target.example"),
    )
    assert job.state is JobState.QUEUED
    assert job.policy_decision == "warn"
    assert job.policy_warnings


def test_acknowledgement_state_is_explicit_and_operator_can_advance_it():
    policy = OperatorPolicy(
        enforcement_mode=EnforcementMode.ACKNOWLEDGE,
        require_risk_acknowledgement=True,
        acknowledgement_at_or_above=RiskLevel.MEDIUM,
    )
    orchestrator = HordeOrchestrator()
    job = orchestrator.prepare_request(
        mission(policy),
        agent(),
        request(risk_level=RiskLevel.HIGH),
    )
    assert job.state is JobState.NEEDS_ACKNOWLEDGEMENT

    orchestrator.acknowledge_job(job)
    assert job.state is JobState.QUEUED
    assert job.policy_reason == "operator acknowledgement recorded"


def test_operator_override_preserves_warning_and_reason():
    policy = OperatorPolicy(
        enforcement_mode=EnforcementMode.STRICT,
        require_target_scope=True,
        allow_operator_override=True,
    )
    job = HordeOrchestrator().prepare_request(
        mission(policy),
        agent(),
        request(
            target="operator-target.example",
            operator_override=True,
            override_reason="scope expanded by operator",
        ),
    )
    assert job.state is JobState.QUEUED
    assert job.override_applied is True
    assert job.override_reason == "scope expanded by operator"
    assert job.policy_warnings


def test_identity_mismatch_remains_a_structural_block():
    policy = OperatorPolicy()
    job = HordeOrchestrator().prepare_request(
        mission(policy),
        agent(),
        request(mission_id="different-mission"),
    )
    assert job.state is JobState.BLOCKED
    assert "identity mismatch" in job.policy_reason


def test_runnable_job_can_produce_evidence():
    policy = OperatorPolicy()
    orchestrator = HordeOrchestrator()
    job = orchestrator.prepare_request(mission(policy), agent(), request())

    def operation() -> Evidence:
        return Evidence(
            evidence_id="e1",
            target="lab.local",
            source="test",
            observed_at="2026-08-24T00:00:00Z",
            observation="operator-controlled result",
            confidence=1.0,
        )

    job, evidence = orchestrator.run_evidence_job(job, operation)
    assert job.state is JobState.COMPLETE
    assert evidence is not None
    assert job.evidence_ids == ["e1"]
