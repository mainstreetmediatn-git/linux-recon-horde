from horde.lifecycle import LifecycleError, LifecycleManager
from horde.models import Agent, AgentState, MemoryRecord, MemoryState


def make_agent(agent_id: str, name: str) -> Agent:
    return Agent(
        agent_id=agent_id,
        name=name,
        role="specialist",
        specialization="http",
        scopes=["lab.local"],
        allowed_tools=["passive-http"],
        memory_namespaces=["engagements/demo"],
        evidence_quality=0.95,
        compliance_score=1.0,
        health_score=1.0,
    )


def test_admission_requires_human_approval():
    manager = LifecycleManager()
    manager.propose(make_agent("a1", "Scout One"))
    try:
        manager.admit("a1", human_approved=False)
    except LifecycleError:
        pass
    else:
        raise AssertionError("admission should require human approval")


def test_retirement_pauses_until_successor_is_active():
    manager = LifecycleManager()
    predecessor = make_agent("old", "Veteran")
    manager.propose(predecessor)
    manager.admit("old", human_approved=True)
    manager.activate("old", judge_approved=True, auditor_approved=True)

    successor = make_agent("new", "Successor")
    manager.create_successor("old", successor)

    memory = MemoryRecord(
        memory_id="m1",
        namespace="engagements/demo",
        title="Known behavior",
        body="Validated passive observation",
        author="old",
        source="test",
        confidence=1.0,
        created_at="2026-08-18T00:00:00Z",
        state=MemoryState.ACTIVE,
    )

    try:
        manager.complete_handoff(
            "old",
            approved_memory=[memory],
            judge_approved=True,
            auditor_approved=True,
            human_approved=True,
        )
    except LifecycleError:
        pass
    else:
        raise AssertionError("retirement must pause while successor is not active")

    manager.activate("new", judge_approved=True, auditor_approved=True)
    retired = manager.complete_handoff(
        "old",
        approved_memory=[memory],
        judge_approved=True,
        auditor_approved=True,
        human_approved=True,
    )
    assert retired.state is AgentState.RETIRED
    assert manager.agents["new"].predecessor_id == "old"
    assert any(event.event_type == "succession.handoff" for event in manager.audit_log)


def test_successor_trigger_uses_health_tenure_or_quality():
    manager = LifecycleManager()
    agent = make_agent("a1", "Scout One")
    manager.propose(agent)
    assert not manager.needs_successor("a1")
    agent.health_score = 0.5
    assert manager.needs_successor("a1")
