from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from .models import Agent, MissionContract


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(slots=True, frozen=True)
class PolicyDecision:
    decision: Decision
    reason: str
    required_approvals: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()


@dataclass(slots=True)
class ConstitutionPolicy:
    """Small, explicit policy engine for Horde constitutional invariants."""

    version: str = "1.0.0"
    rules: dict[str, str] = field(
        default_factory=lambda: {
            "HORD-LAW-001": "deny by default",
            "HORD-LAW-002": "least scoped authority",
            "HORD-LAW-003": "evidence over assertion",
            "HORD-LAW-004": "human approval for high-impact lifecycle actions",
            "HORD-LAW-005": "authorized targets only",
            "HORD-LAW-006": "separation of powers",
            "HORD-LAW-007": "append-only audit for important state changes",
        }
    )

    def evaluate_mission(self, mission: MissionContract) -> PolicyDecision:
        if not mission.authorized:
            return PolicyDecision(
                Decision.DENY,
                "mission is not explicitly authorized",
                rule_ids=("HORD-LAW-001", "HORD-LAW-005"),
            )
        if not mission.target_scope:
            return PolicyDecision(
                Decision.DENY,
                "mission has no explicit target scope",
                rule_ids=("HORD-LAW-002", "HORD-LAW-005"),
            )
        if not mission.required_evidence:
            return PolicyDecision(
                Decision.DENY,
                "mission defines no evidence requirements",
                rule_ids=("HORD-LAW-003",),
            )
        return PolicyDecision(Decision.ALLOW, "mission contract satisfies baseline policy")

    def evaluate_agent_tool_use(self, agent: Agent, *, tool: str, target: str) -> PolicyDecision:
        if target not in agent.scopes:
            return PolicyDecision(
                Decision.DENY,
                "target is outside the agent's explicit scope",
                rule_ids=("HORD-LAW-002", "HORD-LAW-005"),
            )
        if tool not in agent.allowed_tools:
            return PolicyDecision(
                Decision.DENY,
                "tool is not admitted for this agent",
                rule_ids=("HORD-LAW-001", "HORD-LAW-002"),
            )
        return PolicyDecision(Decision.ALLOW, "tool and target are within admitted scope")

    def evaluate_lifecycle_action(self, action: str, approvals: Iterable[str]) -> PolicyDecision:
        high_impact = {"admit", "activate", "promote_successor", "suspend", "retire", "remove"}
        if action not in high_impact:
            return PolicyDecision(Decision.ALLOW, "action is not classified as high-impact")

        given = set(approvals)
        required = {"human"}
        if action in {"activate", "promote_successor", "retire"}:
            required |= {"judge", "auditor"}
        missing = required - given
        if missing:
            return PolicyDecision(
                Decision.REQUIRE_APPROVAL,
                f"missing approvals: {', '.join(sorted(missing))}",
                required_approvals=tuple(sorted(required)),
                rule_ids=("HORD-LAW-004",),
            )
        return PolicyDecision(Decision.ALLOW, "required approvals are present")

    def validate_role_separation(self, role_capabilities: dict[str, set[str]]) -> PolicyDecision:
        exclusive = {"plan", "execute", "judge", "memory_govern", "tool_admit", "audit"}
        for role, capabilities in role_capabilities.items():
            owned = exclusive.intersection(capabilities)
            if len(owned) > 2:
                return PolicyDecision(
                    Decision.DENY,
                    f"role {role} owns too many constitutional powers: {', '.join(sorted(owned))}",
                    rule_ids=("HORD-LAW-006",),
                )
        return PolicyDecision(Decision.ALLOW, "role capabilities preserve separation of powers")
