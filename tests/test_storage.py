from horde.models import Agent, Evidence, MemoryRecord, MemoryState, MissionContract
from horde.storage import SQLiteStore


def test_store_persists_domain_records_across_reopen(tmp_path):
    db = tmp_path / "horde.db"
    store = SQLiteStore(db)
    agent = Agent(
        agent_id="a1",
        name="Scout One",
        role="specialist",
        specialization="http",
        scopes=["lab.local"],
    )
    mission = MissionContract(
        mission_id="m1",
        objective="Inspect approved lab metadata",
        target_scope=["lab.local"],
        success_criteria=["evidence recorded"],
        constraints=["passive-first"],
        participant_ids=["a1"],
        required_evidence=["http-headers"],
        allowed_tools=["passive-http"],
        approval_gates=["human"],
        report_requirements=["technical-summary"],
        authorized=True,
    )
    evidence = Evidence(
        evidence_id="e1",
        target="lab.local",
        source="test",
        observed_at="2026-08-18T00:00:00Z",
        observation="header present",
        confidence=1.0,
    )
    memory = MemoryRecord(
        memory_id="mem1",
        namespace="engagements/demo",
        title="Observation",
        body="Validated lab observation",
        author="a1",
        source="e1",
        confidence=1.0,
        created_at="2026-08-18T00:00:00Z",
        state=MemoryState.ACTIVE,
        evidence_ids=["e1"],
    )

    store.save_agent(agent)
    store.save_mission(mission)
    store.save_evidence(evidence)
    store.save_memory(memory)
    store.append_audit("agent.saved", "a1", "2026-08-18T00:00:00Z", {"source": "test"})
    store.close()

    reopened = SQLiteStore(db)
    assert reopened.get_agent("a1")["name"] == "Scout One"
    assert reopened.get_mission("m1")["authorized"] is True
    assert reopened.list_evidence()[0]["evidence_id"] == "e1"
    assert reopened.list_memory()[0]["state"] == "active"
    assert reopened.list_audit()[0]["event_type"] == "agent.saved"
    reopened.close()


def test_engagement_and_environment_metadata_are_durable(tmp_path):
    store = SQLiteStore(tmp_path / "horde.db")
    store.save_engagement(
        "eng-1",
        "Approved Lab",
        "active",
        True,
        {"targets": ["lab.local"], "owner": "operator"},
    )
    store.save_environment(
        "env-1",
        "Passive Python",
        "healthy",
        {"language": "python", "ephemeral": True},
    )

    assert store.get_engagement("eng-1")["authorized"] is True
    assert store.list_environments()[0]["payload"]["ephemeral"] is True
    store.close()
