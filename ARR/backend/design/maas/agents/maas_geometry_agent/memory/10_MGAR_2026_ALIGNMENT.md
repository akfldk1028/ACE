# MGA_R 2026 alignment

Primary reference: Deng, Wang, Ji, and Long (2026), *Parallel typological
optimization in architectural design: a ResNet-enhanced island-based
evolutionary algorithm*, DOI `10.1080/13467581.2026.2635250`.

The authoritative local review is
`collected_papers/maas/SELECTED_PRIMARY_PAPER_MGAR_2026.md`. It was prepared
from the publisher full-text and indexed paper content. The MGA_R PDF is not
stored locally, and no author-published code, training dataset, or model
weights were confirmed. `EvoMass_2024.pdf` is a different earlier paper.
Never claim that 25_ACE ports or reproduces the authors' implementation.

## What 25_ACE adopts

- preserve several explicit phenotype populations instead of allowing one
  high-fitness silhouette to dominate the whole search;
- assign islands from measured final geometry, not from an authored family
  label or parameter distance alone;
- keep law, parking, topology, capacity, and identity as independent hard
  gates before an individual can become an island survivor;
- compare candidates under the same evaluation budget;
- retain an append-only generation/frontier history and replenish the
  phenotype island that is actually deficient;
- allow migration when final certified geometry belongs to a different island
  than the authored intent.

## What 25_ACE does not adopt yet

- no ResNet claim: the paper's six-class dataset and weights are unavailable;
- no invented classifier confidence or fake learned labels;
- no 1,200-3,000 generation run until bounded diagnostics demonstrate useful
  per-generation yield;
- no Ladybug-equivalence claim for the existing proxy metrics;
- no L/U/Regular/Fragmented/Courtyard/Hybrid quota copied as a universal
  architectural truth;
- no deterministic mutation that authors morphology. Codex/OAuth LLM remains
  the source of each new typed AST; deterministic code may classify, retain,
  reject, migrate, and request a missing island.

## Current evidence and next use

C112 proves the bounded flow can select three lawful non-stepped masses, but
all three are measured `wedge_like=true`; cards 1 and 2 remain visually close.
This is a convergence signal, not a reason to generate a broad random batch.
Target five now has an explicit final-mesh island contract: at least four body
phenotypes, no more than two cards per phenotype, at least four body/roof
signatures, no more than one visibly stepped card, and final pair distance at
least `0.10`. The existing measured wedge cap allows at most three of five, so
at least two must be non-wedge. Keep valid survivors, identify missing
non-wedge islands, request only those authored families, and re-run the same
law/parking/capacity/identity gates. Do not attempt canonical twenty until this
five-card contract passes without a broad low-yield sweep.

The paper's reported diversity value `3.44` is its mean genotypic distance. It
is not an architectural-quality score and must not be compared numerically to
25_ACE final-mesh distance thresholds.
