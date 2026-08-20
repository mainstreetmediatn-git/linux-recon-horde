# Connections and Tool-Calling Map

This document records the external connections used during Horde development. It is an operator map, not a place to store credentials.

## GitHub

Primary engineering source of truth.

Repository:

`mainstreetmediatn-git/linux-recon-horde`

Current working branch:

`recovered-architecture`

Used for:

- repository inspection
- branch inspection
- reading source files
- creating/updating source files
- tests and workflows
- pull requests
- CI status
- issues/review when needed

Operational rule:

- All Horde code writes belong only in the Linux Recon Horde repository.
- Do not write to CIVITAS, SentinalOS, or unrelated repositories as part of Horde work.
- `horde/cli.py` is protected and must not be modified without explicit human approval.

## Replit

App used for rapid product/UI prototyping and implementation assistance.

Known app:

- title observed: `Linux Recon Hub`
- Repl ID: `552156ce-7208-4d1b-a379-5cb03e169e42`

Used for:

- operator-console UI
- enterprise dashboard design
- product-level iteration
- app inspection through Replit Agent
- safe implementation prompts

Important limitation:

Replit-generated or modified behavior should not automatically be treated as GitHub source-of-truth code until it is verified and intentionally synchronized into this repository.

## Google Drive

Read-only design/reference source when explicitly needed.

Used for:

- recovering original Horde architecture notes
- reading the App Vault source map
- reading CIVITAS constitutional doctrine and lifecycle concepts as reference

Boundary:

Drive reference material does not create permission to merge unrelated systems into Horde.

## CIVITAS GitHub repository

Reference-only during Horde work.

Used to understand:

- persistent agent/citizen identity
- lifecycle states and retirement concepts
- constitutional governance
- human sovereignty
- separation of powers
- memory integrity
- audit requirements
- succession-oriented continuity concepts

Boundary:

Do not write to the CIVITAS repository from a Horde task.

## OpenAI Platform

Used for OpenAI API-key setup and project/key targeting when the operator requests OpenAI-backed agent functionality.

Credential handling:

- Real API keys must never be committed to Git.
- Local keys belong in ignored environment files or a proper secret store.
- CI keys belong in GitHub Actions Secrets.
- Expected secret name for Horde: `OPENAI_API_KEY`.
- Never print, echo, persist, or place the raw key into documentation.

## GitHub Actions Secrets

Preferred CI secret location.

Expected repository secret:

`OPENAI_API_KEY`

Workflows may reference the value as the GitHub Actions secret named `OPENAI_API_KEY`; repository documentation should never contain the raw value.

## Image generation / design reference

Image generation was used to create the approved dark futuristic Horde operator-console visual direction.

The design concept includes:

- grouped left navigation
- operation/environment header
- metric cards
- agent status grid
- mission/finding/activity panels
- constitution/memory/human-oversight/audit status strip
- dark navy/black base with purple, green, blue, amber, and red status accents

This visual reference is product guidance; backend truth must come from persisted Horde services.

## Tool-calling principle

Use the narrowest connected tool that owns the requested data/action:

- GitHub changes -> GitHub connection
- Replit app changes -> Replit connection
- Drive reference documents -> Google Drive connection
- OpenAI API key setup -> OpenAI Platform connection

Do not substitute unrelated tools when the owning connection is available.
