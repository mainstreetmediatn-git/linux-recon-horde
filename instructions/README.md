# Linux Recon Horde — Operator & Build Instructions

This folder is the durable operating brief for Linux Recon Horde.

It exists so a human operator, Codex, Replit Agent, or another approved build agent can understand the project before making changes.

## Read order

1. `CONCEPT.md` — what the Horde is and what it is not.
2. `CURRENT_STATE.md` — what is actually implemented now.
3. `HARDENING.md` — what must be strengthened before enterprise use.
4. `NEXT_STEPS.md` — logical build order from the current state.
5. `CONNECTIONS.md` — connected services and how they are used for tool calling.
6. `OPERATING_RULES.md` — repository boundaries, safety, branch rules, and protected files.

## Core doctrine

- Human over system.
- Constitution over mission.
- Law over tool.
- Evidence over assertion.
- Authorized targets only.
- Deny by default.
- Separate planning, execution, judging, memory governance, tool admission, and audit powers.
- Persist evidence, decisions, lifecycle transitions, and approvals.
- Agents must have a lifecycle, succession plan, and auditable lineage.

## Repository boundary

All implementation work for this project belongs in:

`mainstreetmediatn-git/linux-recon-horde`

CIVITAS and SentinalOS may be read as design references when explicitly needed, but they are separate systems and must not be modified as part of Horde work.

## Protected file

`horde/cli.py` is frozen by operator instruction. Do not modify it unless the human operator explicitly revokes that instruction.
