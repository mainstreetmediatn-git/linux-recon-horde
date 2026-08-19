from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from .models import Evidence


class FindingState(str, Enum):
    OPEN = "open"
    CONTESTED = "contested"
    CONFIRMED = "confirmed"
    DUPLICATE = "duplicate"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


@dataclass(slots=True)
class JudgedFinding:
    finding_id: str
    target: str
    title: str
    severity: str
    confidence: float
    evidence_ids: list[str]
    state: FindingState
    reasons: list[str] = field(default_factory=list)
    duplicate_of: str | None = None


class EvidenceJudge:
    """Correlates evidence without performing any reconnaissance itself."""

    def correlate(self, evidence: Iterable[Evidence], *, title: str, severity: str = "info") -> JudgedFinding:
        items = list(evidence)
        if not items:
            raise ValueError("at least one evidence item is required")

        targets = {item.target for item in items}
        if len(targets) != 1:
            return JudgedFinding(
                finding_id=f"finding:{title.lower().replace(' ', '-')}:{items[0].target}",
                target=items[0].target,
                title=title,
                severity=severity,
                confidence=0.0,
                evidence_ids=[item.evidence_id for item in items],
                state=FindingState.CONTESTED,
                reasons=["evidence refers to multiple targets"],
            )

        confidence = sum(max(0.0, min(1.0, item.confidence)) for item in items) / len(items)
        distinct_sources = {item.source for item in items}
        reasons: list[str] = []
        state = FindingState.OPEN

        if len(distinct_sources) >= 2 and confidence >= 0.85:
            state = FindingState.CONFIRMED
            reasons.append("corroborated by independent evidence sources")
        elif confidence < 0.60:
            state = FindingState.NEEDS_HUMAN_REVIEW
            reasons.append("confidence below automatic acceptance threshold")
        else:
            reasons.append("single-source or moderate-confidence evidence")

        return JudgedFinding(
            finding_id=f"finding:{title.lower().replace(' ', '-')}:{items[0].target}",
            target=items[0].target,
            title=title,
            severity=severity,
            confidence=round(confidence, 4),
            evidence_ids=[item.evidence_id for item in items],
            state=state,
            reasons=reasons,
        )

    def suppress_duplicates(self, findings: Iterable[JudgedFinding]) -> list[JudgedFinding]:
        seen: dict[tuple[str, str], str] = {}
        output: list[JudgedFinding] = []
        for finding in findings:
            key = (finding.target, finding.title.strip().lower())
            if key in seen:
                finding.state = FindingState.DUPLICATE
                finding.duplicate_of = seen[key]
                finding.reasons.append("duplicate target/title pair")
            else:
                seen[key] = finding.finding_id
            output.append(finding)
        return output
