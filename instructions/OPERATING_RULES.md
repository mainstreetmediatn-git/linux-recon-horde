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

## Safety and authorization

- Recon targets must be owned or explicitly authorized.
- Deny by default when authorization is absent or ambiguous.
- Keep mission and agent scopes explicit.
- Tool use must be admitted and scoped.
- Preserve audit records and evidence provenance.
- Do not add credential theft, uncontrolled brute force, malware, persistence, destructive actions, anti-forensics, log wiping, or unsafe external targeting.

## Human authority

High-impact actions require human control, including:

- agent admission
- successor promotion
- retirement
- suspension/removal
- constitutional amendments
- high-impact tool admission
- broad scope expansion

Judge and Auditor review should supplement, not replace, human sovereignty.

## Engineering rules

- Prefer typed domain models.
- Separate domain, persistence, policy, orchestration, judging, and UI concerns.
- Add tests alongside new behavior.
- Do not claim functionality is live until verified.
- Distinguish demo/sample data from persisted/live data.
- Preserve backward compatibility unless intentionally versioning a contract.
- Keep evidence and lifecycle transitions reproducible and auditable.

## Agent lifecycle rule

Never retire an agent in a way that creates an avoidable capability gap.

Normal succession requires:

1. successor candidate creation
2. probation/shadow training
3. approved memory transfer
4. readiness evaluation
5. Judge/Auditor review
6. human approval
7. overlap/handoff window
8. predecessor retirement
9. archived lineage record

If the successor fails readiness, pause retirement.

## External references

CIVITAS concepts may inform Horde governance, but Horde must remain its own repository, codebase, policies, data, and runtime.

SentinalOS remains a separate runtime/operator system and should not be silently imported into Horde.
