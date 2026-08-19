# Next Logical Steps

This is the preferred build order from the current `recovered-architecture` state.

## Phase 1 — Finish persistence integration

1. Add a repository/service layer that wraps `SQLiteStore`.
2. Make lifecycle state changes transactional and persisted.
3. Persist succession reviews, approvals, incidents, findings, and memory handoffs.
4. Add schema versioning and migrations.
5. Add restart/recovery integration tests.

Definition of done: a process restart does not lose or desynchronize an engagement, mission, agent lifecycle, evidence, finding, approval, or audit event.

## Phase 2 — Harden lifecycle and succession

1. Add an explicit state-transition table.
2. Reject invalid transitions.
3. Add successor readiness records.
4. Add shadow-mission comparison results.
5. Add overlap-window tracking.
6. Add emergency human exception path with mandatory audit record.
7. Add immutable lineage history.

Definition of done: an agent cannot be activated, suspended, succeeded, retired, removed, or archived outside constitutional transition rules.

## Phase 3 — Complete Judge and Auditor services

1. Persist findings.
2. Normalize finding signatures.
3. Add contradiction/freshness/source-independence scoring.
4. Add duplicate suppression.
5. Add Judge verdicts and dissent.
6. Add Auditor reviews for policy, lifecycle, and tool-use records.
7. Route uncertain findings to human review.

Definition of done: every reportable finding can be traced from report -> Judge decision -> normalized evidence -> raw source -> producing agent/environment/mission.

## Phase 4 — Build durable orchestration

1. Persist jobs and state transitions.
2. Add durable queue/worker abstraction.
3. Add timeouts, bounded retry, cancellation, and idempotency.
4. Re-check authorization immediately before execution.
5. Bind every job to mission, agent, target, tool admission, environment, and policy decision.
6. Route resulting evidence automatically into judging.

Definition of done: specialist work can survive process restarts and is always scope/policy checked.

## Phase 5 — Engagement and managed environment control plane

1. Promote engagement/environment metadata into typed domain models.
2. Add authorization records and expiration.
3. Add environment templates for Python, Go, Rust, Bash, and container tools.
4. Track exact dependency/tool versions.
5. Add health and reproducibility fingerprints.
6. Add per-agent and per-mission assignments.
7. Add secrets-reference fields without storing secret values.

Definition of done: the operator can prove exactly where and with what versions an evidence item was produced.

## Phase 6 — Expand safe specialist interfaces

Add specialists incrementally, keeping centralized scope/policy enforcement:

1. DNS specialist
2. TLS specialist
3. HTTP metadata/header/cookie specialist
4. technology fingerprint specialist
5. observed-route/content specialist
6. public subdomain metadata specialist
7. bounded TCP service metadata specialist for approved environments
8. bounded UDP metadata specialist with explicit load policy
9. version-detection adapter

Each specialist must output structured evidence and must not bypass mission or agent scope.

## Phase 7 — API, RBAC, and operator UI integration

1. Add authenticated service/API layer.
2. Add administrator/operator/reviewer/auditor/read-only roles.
3. Wire the approved dark Horde operator UI to real backend data.
4. Add engagements, missions, agents, lifecycle, succession, findings, evidence, reports, environments, constitution, and audit screens.
5. Clearly distinguish live data from fixtures/demo data.

Definition of done: the UI is a view/control layer over the same persisted backend used by tests and services.

## Phase 8 — Enterprise quality gate

1. CI type checking and linting.
2. Python compatibility matrix.
3. migration tests.
4. end-to-end authorized lab fixtures.
5. security review.
6. backup/recovery test.
7. documentation review.
8. release/versioning policy.
9. operator runbook.

## Protected-file rule

Do not modify `horde/cli.py` unless the human operator explicitly authorizes that exact file to be changed.
