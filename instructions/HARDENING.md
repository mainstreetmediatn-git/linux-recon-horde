# Hardening Requirements

The current Horde is a credible backend prototype. The following areas must be hardened before calling it enterprise-ready.

## 1. Persistence integration

- Wire lifecycle transitions directly through a repository/service abstraction so agent state cannot silently diverge from SQLite.
- Persist Judge findings, succession reviews, approvals, incidents, and memory handoffs.
- Add schema versioning/migrations.
- Add transaction boundaries for multi-record operations such as succession handoff.
- Add backup/export and recovery procedures.
- Add integrity checks for audit/evidence records.

## 2. Lifecycle invariants

Add explicit state-transition validation rather than allowing arbitrary mutation.

Required protections include:

- duplicate successor ID rejection
- invalid predecessor-state rejection
- no activation of suspended/removed agents
- no retirement without an active successor unless the human explicitly performs an emergency exception
- no memory handoff of contested, sealed, or superseded records without review
- no successor promotion without readiness evidence
- no silent lineage rewrites
- no role/scope escalation during succession without approval

## 3. Constitution and policy

- Version the Horde Constitution as a durable record.
- Store policy decisions and rule IDs with important actions.
- Add policy regression tests.
- Add explicit tool admission records with version/source/risk/containment metadata.
- Add incident-trigger behavior when constitutional checks fail.
- Add human override records rather than bypass flags.

## 4. Evidence integrity

- Give evidence globally unique identifiers.
- Add hashes/checksums for artifacts.
- Store producer agent, environment, mission, engagement, tool version, and policy decision.
- Distinguish raw evidence, normalized observations, findings, and reports.
- Preserve conflicting evidence instead of overwriting it.
- Add evidence retention states and archival policy.

## 5. Judge/Auditor hardening

- Require Judge output to reference exact evidence IDs.
- Add contradiction detection beyond target mismatch.
- Add freshness/age scoring.
- Add source independence weighting.
- Add duplicate suppression based on normalized signatures rather than only title/target.
- Add explicit dissent/review records.
- Add Auditor inspection of policy decisions, lifecycle transitions, and tool usage.

## 6. Orchestration hardening

- Introduce durable job queue semantics.
- Add retries with bounded limits and reason tracking.
- Add cancellation and timeout policies.
- Add idempotency keys.
- Prevent a job from running after mission authorization is revoked.
- Bind each job to an approved environment and tool version.
- Persist every transition.

## 7. Managed execution environments

- Add explicit environment templates.
- Track interpreter/compiler/tool versions and lockfiles.
- Add health checks and reproducibility fingerprints.
- Isolate secrets from logs and persisted command output.
- Add disposable/ephemeral environment lifecycle.
- Add environment-to-agent and environment-to-engagement assignments.
- Add container isolation adapters without giving containers unrestricted host access.

## 8. Authentication and RBAC

Future API/UI layers need roles such as:

- administrator
- operator
- reviewer/judge
- auditor
- read-only

Enforce authorization server-side, not only in the UI.

## 9. Testing and quality

- Expand lifecycle transition tests.
- Add persistence integration tests.
- Add judging tests.
- Add orchestration tests.
- Add migration tests.
- Add static typing checks.
- Add linting/formatting.
- Add supported Python-version CI matrix.
- Add reproducible test fixtures for authorized demo environments.

## 10. Operational security

- Secrets belong in environment/secret managers, never tracked files.
- Keep `.env` ignored.
- Use GitHub Actions Secrets for CI credentials.
- Never print API keys or tokens in logs.
- Keep auditability intact; do not add trace wiping or anti-forensics.
