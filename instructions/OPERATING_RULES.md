# Operating Rules

These rules govern future work on Linux Recon Horde unless the human operator explicitly overrides them.

## Repository scope

Write only to:

`mainstreetmediatn-git/linux-recon-horde`

for Horde implementation tasks.

Do not modify CIVITAS, SentinalOS, Agent Horde, or unrelated repositories when working on Linux Recon Horde.

## Working branch

Current implementation branch:

`recovered-architecture`

Do not assume `main` contains the active implementation until the relevant pull request has been intentionally merged.

## Protected file

`horde/cli.py` is frozen.

- Do not edit it.
- Do not reformat it.
- Do not replace it while refactoring adjacent modules.
- Do not include it in automated bulk rewrites.
- Only modify it after explicit human instruction naming that file.

## Secrets

- Never commit raw API keys, passwords, tokens, private keys, or credentials.
- Keep `.env` ignored.
- Use `.env.example` only for empty variable names/placeholders.
- Use GitHub Actions Secrets for CI secrets.
- Use `OPENAI_API_KEY` as the expected OpenAI secret name unless the operator changes it.
- Never place secret values in instructions, issues, PR descriptions, logs, evidence, or reports.

## Operator-defined engagement policy

Horde does not maintain a second hidden rules-of-engagement layer that silently overrides the operator's configuration.

The operator controls engagement behavior through `OperatorPolicy`, including:

- enforcement mode: `advisory`, `acknowledge`, or `strict`
- whether explicit mission authorization is required
- whether target scope is enforced
- whether tool admission is enforced
- whether module admission is enforced
- whether risk acknowledgement is required
- the risk threshold at which acknowledgement begins
- whether operator override is permitted

Risk levels, target scope, tool lists, module lists, and role concentration remain visible as metadata even when they are not configured as blocking controls.

### Enforcement semantics

- `advisory` — policy findings are surfaced and recorded but do not block a runnable job.
- `acknowledge` — configured findings pause the job until operator acknowledgement.
- `strict` — configured findings block the job unless an enabled operator override is applied.

Operator override is a first-class state. When enabled, Horde records the fact that an override occurred, preserves the underlying warnings, and stores the operator-provided reason rather than pretending the original policy finding never happened.

Structural integrity checks, such as mismatched mission or agent identity, remain errors because they indicate internally inconsistent data rather than a rules-of-engagement choice.

## Human authority

The operator is the authority over configured engagement controls. Judge, Auditor, agent, and policy services provide evaluation, evidence, warnings, and history; they do not silently replace operator policy with a separate hidden ruleset.

Lifecycle approvals and role-separation checks are recorded as metadata and may be promoted into enforcement by future operator policy settings rather than being unconditionally hardcoded.

## Engineering rules

- Prefer typed domain models.
- Separate domain, persistence, policy, orchestration, judging, and UI concerns.
- Add tests alongside new behavior.
- Do not claim functionality is live until verified.
- Distinguish demo/sample data from persisted/live data.
- Preserve backward compatibility unless intentionally versioning a contract.
- Keep policy decisions, overrides, evidence, and lifecycle transitions reproducible and auditable.
- Do not hide policy warnings merely because the operator chose advisory mode or applied an override.

## Agent lifecycle rule

Agent lifecycle behavior should be configurable rather than treated as an independent engagement gate. Lifecycle transitions should preserve lineage and history so the operator can understand what changed and why.

## External references

CIVITAS concepts may inform Horde governance, but Horde must remain its own repository, codebase, policies, data, and runtime.

SentinalOS remains a separate runtime/operator system and should not be silently imported into Horde.
