# ARR Shared Agent Architecture

`ARR/backend/agents/` is the shared multi-agent control plane. It owns common
memory, A2A contracts, discovery, routing, logs, persistence, and orchestration.
It is not one specialist agent.

## Specialist repository standard

`elevationAgent/` is the checked-in structural reference for every future
specialist agent repository. New specialists such as `massAgent`, `planAgent`,
`lawAgent`, and `facadeAgent` must be sibling folders under `backend/agents/`
and expose the same git-native surfaces:

```text
{specialistAgent}/
  .git/                   # independent auditable history when provisioned
  agent.yaml              # identity, model, tools, runtime
  SOUL.md                 # stable responsibility and design intent
  RULES.md                # non-negotiable boundaries
  memory/MEMORY.md        # agent-private persistent memory
  skills/                 # reusable specialist procedures
  agents/                 # private child-agent definitions
  src/                    # runtime and adapters
  test/                   # contract and behavior tests
  docs/                   # specialist documentation
  examples/               # bounded examples, never authority
```

The template copies structure, not identity or history. A new specialist must
initialize its own `.git`, `name`, `description`, SOUL, RULES, memory, tools,
skills, tests, and capability contract. Existing example/task content in
`elevationAgent/memory/MEMORY.md` must never be inherited.

## Shared versus private memory

- `backend/agents/memory/` is cross-agent shared memory and stable coordination
  policy. It contains no agent-private chain-of-thought, credentials, or
  unverified claims.
- `{specialistAgent}/memory/` belongs only to that specialist and is versioned
  with its independent repository.
- Shared facts cross the boundary through typed records with source agent,
  timestamp, schema version, evidence IDs, and status.
- MASS-related handoffs use `run_id`, `program_hash`, `geometry_hash`, PNU,
  artifact URLs, gate status, and VLM truth state as stable identities.

## Domain engine boundary

`ARR/backend/design/maas/` is the shared architectural massing domain engine.
It owns GeometryProgram, compiler, BOOK language, legal/program projection,
rendering, VLM evaluation, and outcome graph code. A future `massAgent/` owns
the agent identity, tools, memory, and collaboration behavior that invoke this
engine. Domain-engine modules are not themselves independent GitAgent repos.

Existing `design/maas/agents/` folders are legacy/in-process MAAS adapters.
They remain until an explicit migration preserves Django imports and tests.
Do not duplicate live authority across both locations: each capability must
declare one executable owner and one adapter path.

## Planned collaboration

```text
shared control plane
  -> massAgent: exact GeometryProgram + MASS render + causal passport
  -> planAgent: floor-plan artifact bound to geometry_hash
  -> elevationAgent: elevation/image artifact bound to geometry_hash
  -> lawAgent: jurisdiction and compliance evidence bound to PNU + geometry_hash
  -> critic/review agents: typed findings and repair requests
  -> selector/orchestrator: accepts only materialized, evidence-linked outputs
```

An image applied to a MASS, an elevation, or a plan must never replace the
authoritative GeometryProgram. It is a derived artifact attached by hash.
