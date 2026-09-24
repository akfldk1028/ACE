# Problem Context for Proposal

## One-Sentence Problem

Architectural design automation remains difficult because early design alternatives must satisfy many interdependent legal, geometric, parking, and performance constraints, while existing generative or rule-checking systems usually handle generation and verification separately.

## Non-Technical Explanation

In early architectural design, the designer does not simply draw a building shape. The designer must repeatedly ask:

- Is this use allowed on this parcel?
- What is the maximum buildable area?
- Does the design satisfy BCR and FAR?
- Does the building violate setback or road constraints?
- Does the mass violate daylight or slant-plane conditions?
- How many parking spaces are legally required?
- Can those parking spaces actually fit in the site geometry?
- If one condition is repaired, does another condition break?
- What legal basis supports the final design decision?

The practical difficulty is that these questions are connected. A change in mass shape can affect FAR, parking, daylight, road constraints, and program feasibility at the same time.

## Why the Law Is Hard

Korean building-related regulation is layered and fragmented:

- Building Act
- Enforcement Decree of the Building Act
- Enforcement Rules
- Parking Lot Act
- Enforcement Decree and Rules for parking
- Local government ordinances
- Zoning and land-use restrictions
- Road and adjacent-site constraints
- Daylight and height restrictions
- BCR/FAR and use-specific conditions

These rules are not just text. Many of them become geometric constraints. For example, parking count is a legal calculation, but parking feasibility is a geometric layout problem.

## Why a Single AI Is Not Enough

A single LLM or agent should not be trusted to invent legal geometry. The tasks are heterogeneous:

- Legal retrieval and interpretation
- Parking count and layout verification
- Candidate generation
- Geometry repair
- Performance comparison
- Evidence summarization
- Final design review

The proposal should argue for specialized agents connected to deterministic tools, not an all-knowing agent.

## Why Multi-Agent Collaboration Helps

The multi-agent structure gives each role a clear responsibility:

- Law Agent finds relevant laws, decrees, rules, and ordinance evidence.
- Parking Agent computes required parking and checks layout feasibility.
- Design/MAAS Agent generates design alternatives.
- Geometry Agent repairs candidate geometry based on violations.
- Review Agent summarizes pass/fail status, evidence, and final decisions.

The value is not just parallelism. The value is accountable division of labor:

- Each agent produces a typed output.
- Each decision can reference evidence.
- Failed candidates can produce repair requests.
- Candidate lineage can be traced.
- Final decisions can be explained.

## Why Graph DB Is Needed

A relational table or plain document is weak for this because the important information is relational:

- Parcel -> zoning -> applicable law
- Law article -> constraint -> validator
- Candidate -> generated geometry -> metric result
- Candidate -> violation -> repair request
- Agent review -> evidence artifact -> final decision
- Candidate -> parent candidate -> mutation/operator lineage

Graph DB should be explained as the memory structure that preserves why a design passed or failed.

## Parking Example for Proposal

Parking is a strong example because it is easy for non-engineering reviewers to understand.

Two different questions exist:

1. How many parking spaces are legally required?
2. Can those parking spaces actually be placed inside the design geometry?

The first is legal/rule calculation. The second is geometric feasibility. A good proposal can use parking to show why law, geometry, and agent collaboration must be connected.

## Research Gap Statement

Existing studies have made progress in generative design, optimization-based massing, code compliance, and AI-based design support. However, a gap remains in connecting these parts into a single workflow where:

- design alternatives are generated,
- legal and geometric constraints are verified,
- violations produce repair requests,
- multiple specialized agents collaborate,
- and the legal/design evidence is stored as traceable graph data.

