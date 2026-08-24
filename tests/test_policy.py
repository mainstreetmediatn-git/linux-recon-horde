from horde.models import (
    Agent,
    EnforcementMode,
    ExecutionRequest,
    MissionContract,
    OperatorPolicy,
    RiskLevel,
)
from horde.policy import ConstitutionPolicy, Decision


def make_mission(*, authorized: bool = False, policy: OperatorPolicy | None = None) -> MissionContract:
    return MissionContract(
        mission_id="m1",
        objective="Operator-defined assessment",
        target_scope=["lab.local"],
        success_criteria=["result recorded"],
        constraints=[],
        participant_ids=["a1"],
        required_evidence=[],
        allowed_tools=["operator-tool"],
        approval_gates=[],
        report_requirements=[],
        authorized=authorized,
        allowed_modules=["mod-1"],
        operator_policy=policy or OperatorPolicy(),
    )


def make_agent() -> Agent:
    return Agent(
        agent_id="a1",
        name="Operator Agent",
        role="specialist",
        specialization="operator-selected",
        scopes=["lab.local"],
        allowed_tools=["operator-tool"],
    )


def make_request(**overrides) -> ExecutionRequest:
    data = dict(
        request_id="r1",
        mission_id="m1",
        agent_id="a1",
        target="lab.local",
        module_id="mod-1",
        tool="operator-tool",
        risk_level=RiskLevel.LOW,
        risk_acknowledged=False,
        operator_override=False,
        override_reason=None,
    )
    data.update(overrides)
    return ExecutionRequest(**data)


def test_default_policy_does_not_impose_hidden_authorization_gate():
    decision = ConstitutionPolicy().evaluate_mission(make_mission(authorized=False))
    assert decision.decision is Decision.ALLOW


def test_advisory_mode_warns_but_does_not_block_configured_scope_findings():
    policy = OperatorPolicy(
        enforcement_mode=EnforcementMode.ADVISORY,
        require_target_scope=True,
        require_tool_admission=True,
    )
    mission = make_mission(policy=policy)
    request = make_request(target="outside.example", tool="different-tool")

    decision = ConstitutionPolicy().evaluate_request(mission, make_agent(), request)
    assert decision.decision is Decision.WARN
    assert len(decision.warnings) >= 2


def test_acknowledgement_mode_can_gate_risk_when_operator_configures_it():
    policy = OperatorPolicy(
        enforcement_mode=EnforcementMode.ACKNOWLEDGE,
        require_risk_acknowledgement=True,
        acknowledgement_at_or_above=RiskLevel.HIGH,
    )
    mission = make_mission(policy=policy)
    request = make_request(risk_level=RiskLevel.HIGH)

    decision = ConstitutionPolicy().evaluate_request(mission, make_agent(), request)
    assert decision.decision is Decision.REQUIRE_ACKNOWLEDGEMENT


def test_strict_mode_enforces_only_operator_enabled_controls():
    policy = OperatorPolicy(
        enforcement_mode=EnforcementMode.STRICT,
        require_explicit_authorization=True,
        require_module_admission=True,
    )
    mission = make_mission(authorized=False, policy=policy)
    request = make_request(module_id="not-admitted")

    decision = ConstitutionPolicy().evaluate_request(mission, make_agent(), request)
    assert decision.decision is Decision.DENY


def test_operator_override_is_first_class_when_enabled():
    policy = OperatorPolicy(
        enforcement_mode=EnforcementMode.STRICT,
        require_target_scope=True,
        allow_operator_override=True,
    )
    mission = make_mission(policy=policy)
    request = make_request(
        target="operator-selected.example",
        operator_override=True,
        override_reason="Operator expanded engagement scope",
    )

    decision = ConstitutionPolicy().evaluate_request(mission, make_agent(), request)
    assert decision.decision is Decision.ALLOW
    assert decision.override_applied is True
    assert decision.warnings


def test_agent_metadata_mismatch_is_advisory_not_an_independent_block():
    policy = ConstitutionPolicy()
    agent = make_agent()
    assert policy.evaluate_agent_tool_use(agent, tool="operator-tool", target="lab.local").decision is Decision.ALLOW
    assert policy.evaluate_agent_tool_use(agent, tool="different-tool", target="lab.local").decision is Decision.WARN


def test_role_concentration_is_reported_as_advisory_metadata():
    result = ConstitutionPolicy().validate_role_separation(
        {"operator-agent": {"plan", "execute", "judge", "audit"}}
    )
    assert result.decision is Decision.WARN
    assert result.warnings
