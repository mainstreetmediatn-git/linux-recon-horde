from horde.models import Agent, MissionContract
from horde.policy import ConstitutionPolicy, Decision


def make_mission(*, authorized: bool = True) -> MissionContract:
    return MissionContract(
        mission_id="m1",
        objective="Inspect approved lab metadata",
        target_scope=["lab.local"],
        success_criteria=["evidence recorded"],
        constraints=["passive-first"],
        participant_ids=["a1"],
        required_evidence=["headers"],
        allowed_tools=["passive-http"],
        approval_gates=["human"],
        report_requirements=["technical-summary"],
        authorized=authorized,
    )


def test_unauthorized_mission_is_denied():
    decision = ConstitutionPolicy().evaluate_mission(make_mission(authorized=False))
    assert decision.decision is Decision.DENY


def test_agent_tool_use_is_scope_and_admission_gated():
    agent = Agent(
        agent_id="a1",
        name="Scout",
        role="specialist",
        specialization="http",
        scopes=["lab.local"],
        allowed_tools=["passive-http"],
    )
    policy = ConstitutionPolicy()
    assert policy.evaluate_agent_tool_use(agent, tool="passive-http", target="lab.local").decision is Decision.ALLOW
    assert policy.evaluate_agent_tool_use(agent, tool="passive-http", target="outside.example").decision is Decision.DENY
    assert policy.evaluate_agent_tool_use(agent, tool="unapproved-tool", target="lab.local").decision is Decision.DENY


def test_retirement_requires_human_judge_and_auditor():
    policy = ConstitutionPolicy()
    result = policy.evaluate_lifecycle_action("retire", approvals={"human", "judge"})
    assert result.decision is Decision.REQUIRE_APPROVAL
    assert set(result.required_approvals) == {"human", "judge", "auditor"}


def test_separation_of_powers_rejects_overpowered_role():
    policy = ConstitutionPolicy()
    result = policy.validate_role_separation(
        {"super-agent": {"plan", "execute", "judge", "audit"}}
    )
    assert result.decision is Decision.DENY
