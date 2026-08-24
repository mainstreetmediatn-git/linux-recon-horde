from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from .models import Agent, EnforcementMode, ExecutionRequest, MissionContract, OperatorPolicy, RiskLevel


class Decision(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    DENY = "deny"
    REQUIRE_ACKNOWLEDGEMENT = "require_acknowledgement"


@dataclass(slots=True, frozen=True)
class PolicyDecision:
    decision: Decision
    reason: str
    warnings: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    override_applied: bool = False


@dataclass(slots=True)
class ConstitutionPolicy:
    """Policy evaluator driven by the operator's configured rules of engagement.

    Horde itself supplies evaluation, warnings, and audit-friendly decisions.
    The operator policy determines which conditions are advisory versus blocking.
    """

    version: str = "2.0.0"
    rules: dict[str, str] = field(
        default_factory=lambda: {
            "HORD-OP-001": "operator policy is authoritative for engagement controls",
            "HORD-OP-002": "configured scope controls are evaluated explicitly",
            "HORD-OP-003": "risk metadata is surfaced to the operator",
            "HORD-OP-004": "operator overrides are explicit and auditable",
            "HORD-OP-005": "important decisions preserve reasons and warnings",
        }
    )

    @staticmethod
    def _risk_rank(risk: RiskLevel) -> int:
        return {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4,
        }[risk]

    @staticmethod
    def _resolve_findings(policy: OperatorPolicy, findings: list[str], *, override: bool, override_reason: str | None) -> PolicyDecision:
        if not findings:
            return PolicyDecision(Decision.ALLOW, "request satisfies configured operator policy")

        if override and policy.allow_operator_override:
            reason = "operator override applied"
            if override_reason:
                reason += f": {override_reason}"
            return PolicyDecision(
                Decision.ALLOW,
                reason,
                warnings=tuple(findings),
                rule_ids=("HORD-OP-004", "HORD-OP-005"),
                override_applied=True,
            )

        if policy.enforcement_mode is EnforcementMode.ADVISORY:
            return PolicyDecision(
                Decision.WARN,
                "configured policy findings are advisory",
                warnings=tuple(findings),
                rule_ids=("HORD-OP-002", "HORD-OP-003"),
            )

        if policy.enforcement_mode is EnforcementMode.ACKNOWLEDGE:
            return PolicyDecision(
                Decision.REQUIRE_ACKNOWLEDGEMENT,
                "operator acknowledgement is required for configured policy findings",
                warnings=tuple(findings),
                rule_ids=("HORD-OP-002", "HORD-OP-003"),
            )

        return PolicyDecision(
            Decision.DENY,
            "request violates configured strict operator policy",
            warnings=tuple(findings),
            rule_ids=("HORD-OP-002",),
        )

    def evaluate_mission(self, mission: MissionContract) -> PolicyDecision:
        policy = mission.operator_policy
        findings: list[str] = []

        if policy.require_explicit_authorization and not mission.authorized:
            findings.append("mission is not explicitly marked authorized")
        if policy.require_target_scope and not mission.target_scope:
            findings.append("mission has no configured target scope")

        return self._resolve_findings(policy, findings, override=False, override_reason=None)

    def evaluate_request(self, mission: MissionContract, agent: Agent, request: ExecutionRequest) -> PolicyDecision:
        policy = mission.operator_policy
        findings: list[str] = []

        if policy.require_explicit_authorization and not mission.authorized:
            findings.append("mission is not explicitly marked authorized")
        if policy.require_target_scope and request.target not in mission.target_scope:
            findings.append("target is outside the mission target scope")
        if policy.require_target_scope and agent.scopes and request.target not in agent.scopes:
            findings.append("target is outside the agent scope")
        if policy.require_tool_admission and request.tool not in mission.allowed_tools:
            findings.append("tool is not admitted by the mission")
        if policy.require_tool_admission and agent.allowed_tools and request.tool not in agent.allowed_tools:
            findings.append("tool is not admitted for the selected agent")
        if policy.require_module_admission and request.module_id not in mission.allowed_modules:
            findings.append("module is not admitted by the mission")

        risk_needs_ack = (
            policy.require_risk_acknowledgement
            and self._risk_rank(request.risk_level) >= self._risk_rank(policy.acknowledgement_at_or_above)
        )
        if risk_needs_ack and not request.risk_acknowledged:
            findings.append(f"{request.risk_level.value} risk has not been acknowledged")

        decision = self._resolve_findings(
            policy,
            findings,
            override=request.operator_override,
            override_reason=request.override_reason,
        )

        if decision.decision is Decision.REQUIRE_ACKNOWLEDGEMENT and request.risk_acknowledged:
            non_risk_findings = [item for item in findings if "risk has not been acknowledged" not in item]
            if not non_risk_findings:
                return PolicyDecision(Decision.ALLOW, "configured acknowledgement requirement satisfied")

        return decision

    def evaluate_agent_tool_use(self, agent: Agent, *, tool: str, target: str) -> PolicyDecision:
        """Compatibility helper. No independent hidden rules are imposed here."""
        findings: list[str] = []
        if agent.scopes and target not in agent.scopes:
            findings.append("target is outside the agent's declared scope")
        if agent.allowed_tools and tool not in agent.allowed_tools:
            findings.append("tool is outside the agent's declared tool set")
        if findings:
            return PolicyDecision(Decision.WARN, "agent metadata mismatch", warnings=tuple(findings))
        return PolicyDecision(Decision.ALLOW, "agent metadata matches request")

    def evaluate_lifecycle_action(self, action: str, approvals: Iterable[str]) -> PolicyDecision:
        """Lifecycle approvals remain metadata-driven; no mandatory approval set is hardcoded."""
        given = tuple(sorted(set(approvals)))
        return PolicyDecision(
            Decision.ALLOW,
            f"lifecycle action '{action}' recorded with approvals: {', '.join(given) if given else 'none'}",
        )

    def validate_role_separation(self, role_capabilities: dict[str, set[str]]) -> PolicyDecision:
        """Role separation is now advisory information for the operator."""
        warnings: list[str] = []
        exclusive = {"plan", "execute", "judge", "memory_govern", "tool_admit", "audit"}
        for role, capabilities in role_capabilities.items():
            owned = exclusive.intersection(capabilities)
            if len(owned) > 2:
                warnings.append(f"role {role} owns multiple powers: {', '.join(sorted(owned))}")
        if warnings:
            return PolicyDecision(Decision.WARN, "role concentration detected", warnings=tuple(warnings))
        return PolicyDecision(Decision.ALLOW, "role capability distribution recorded")
