# MAAS Component-Graph / MAP-Elites / Mass-Brain Independent Audit

Updated: 2026-07-15 KST

Purpose: give a future AI session a code-grounded answer to these questions:

1. Is ARR already doing component-graph MAP-Elites?
2. Does the VLM actually revise geometry, or only rank pictures?
3. Is accepted design memory automatically learned across runs?
4. Would adding another Grasshopper-like evolutionary graph system improve creativity?
5. What should Mass-Brain and GRL own without duplicating ARR?

This is a point-in-time audit, not a claim that every newer artifact is valid.
Do not accept the verdict without checking the code and the newest result JSON/PNG.

## Executive verdict

The short answer is **yes, with important qualifications**.

ARR already contains and executes a component-graph, constrained
MAP-Elites-like quality-diversity loop. The offline loop authors or reloads
executable graphs, compiles them to geometry, applies deterministic gates,
places candidates in behavior cells, asks a VLM to score/criticize them,
applies typed graph edits, recompiles the children, rejects edits that do not
change geometry, rescores the children, and retains qualifying improvements.

It is not canonical MAP-Elites in every detail. The production frontier keeps
multiple representatives per coarse cell and the final selection is a
constraint-aware portfolio selector. The most accurate name is:

> component-graph constrained MAP-Elites-like quality-diversity search with a
> VLM-guided typed graph-revision loop

The system is also not autonomous continual learning across unrelated CLI
runs. Accepted executable graphs are written to durable JSON artifacts and can
be reused, but the next run currently has to receive those artifact paths
explicitly. The offline quality-diversity board does not by itself prove the
separate legal/parking service projection.

Therefore, a second independent MAP-Elites optimizer is likely to duplicate
the existing search. The higher-value work is to broaden the executable graph
representation and make Mass-Brain persist, retrieve, compare, and supply the
existing accepted graph archive across projects. GRL should remain the graph
contract/projection/query/evidence layer, not silently become the geometry
generator or the optimization authority.

## Truth table

| Question | Verdict on 2026-07-15 | Evidence / qualification |
|---|---|---|
| Does ARR have executable component graphs? | Yes | `grammar/component_graph.py`, sequences compiled through SourceMass |
| Is there a behavior-cell archive? | Yes | `GraphBehaviorArchive` stores the best score per behavior key |
| Is this MAP-Elites? | MAP-Elites-like constrained hybrid | one-best cell archive plus a multi-elite bounded frontier and downstream portfolio constraints |
| Is the archive used by the live offline loop? | Yes | instantiated and consumed in `program_massing/vlm_a2a.py` |
| Does VLM feedback reach graph parameters? | Yes, for supported typed edits | directive -> graph edit -> compile -> geometry-difference test -> rescore |
| Has a VLM graph edit ever improved an accepted child? | Yes, at least one recorded case | v88 records a bend control-point child improving VLM `0.4233 -> 0.575` while program score remained `0.959` |
| Are all edit/operator families proven useful? | No | one successful family does not validate every topology, section, void, roof, or cluster edit |
| Are accepted graphs durable? | Yes, as JSON/cache artifacts | output includes `accepted_sequences` |
| Does every new run automatically retrieve all past elites? | No | explicit `--accepted-seed-from`, `--feedback-from`, and cache arguments are required |
| Is there an autonomous global learning database? | Not in the audited offline path | durable artifacts exist; automatic cross-run/cross-project retrieval remains a Mass-Brain responsibility |
| Does the offline board run final law/parking projection? | No | recent v90-v94 memory records `legal/parking projection = not_run` |
| Does GRL generate or optimize geometry? | No | current integration describes GRL as evidence/lineage/query, after archive selection |
| Should Mass-Brain replace ARR's archive? | No | it should index and retrieve accepted executable graphs, outcomes, feedback and lineage |

## Verified execution path

The path to inspect is:

```text
fresh LLM-authored graphs
  + explicitly supplied accepted graphs from prior results
  -> exact graph compilation to SourceMass
  -> capacity/program/geometry hard gates
  -> GraphBehaviorArchive and bounded behavior frontier
  -> preview rendering and VLM scoring
  -> typed critic directive
  -> apply_critic_graph_edits
  -> child graph recompilation
  -> reject graph edit when source geometry is unchanged
  -> child VLM rescore and program-fit comparison
  -> retain accepted parent/child geometry non-destructively
  -> constrained final portfolio selection
  -> result JSON + accepted_sequences + review PNG + accepted PNG + GRL JSON
```

Primary code:

- `ARR/backend/design/maas/program_massing/graph_archive.py`
- `ARR/backend/design/maas/program_massing/vlm_a2a.py`
- `ARR/backend/design/maas/agents/orchestrator/generative_loop.py`
- `ARR/backend/design/maas/agents/llm_architect_agent/graph_revision.py`
- `ARR/backend/design/maas/program_massing/adaptive_loop.py`
- `scripts/run_neighborhood_vlm_a2a.py`

### Behavior descriptor

`graph_behavior_key()` currently includes:

1. language group;
2. formal principle;
3. primary graph verb;
4. branch degree;
5. curved versus planar evidence;
6. void count;
7. height-level count;
8. coverage bin.

`GraphBehaviorArchive.add()` retains the higher-scoring elite for an exact
cell. `bounded_behavior_frontier()` intentionally retains up to several
representatives per cell, then fills a minimum frontier from globally ranked
candidates. This is deliberate: a single winner in a coarse architectural
cell loses meaningful geometric alternatives before expensive morphology and
visual comparisons.

### Why this is not pure canonical MAP-Elites

The final system mixes several mechanisms:

- behavior cell occupancy and replacement;
- scalar candidate scores;
- a multi-representative frontier per cell;
- pose-invariant morphology and silhouette duplicate rejection;
- language/topology/capacity quotas;
- fresh versus persisted and authored coverage;
- constrained portfolio selection.

This is legitimate quality-diversity engineering, but a paper or presentation
must not claim an unmodified canonical MAP-Elites implementation unless an
experiment explicitly isolates and verifies that algorithm.

## VLM closed-loop status

The current offline VLM path is more than image reranking.

`vlm_a2a.py` calls `critic_directive_from_feature()`, applies
`apply_critic_graph_edits()`, recompiles each proposed child, and calls
`_same_source_geometry()` to reject edits that only change graph prose or
metadata. Recompiled children are scored again. A child is accepted only when
it satisfies the hard gates and the configured improvement/program-fit
conditions. A geometry-keyed archive keeps distinct scored parent and child
forms so one revision does not erase other useful morphology.

The v88 evidence reported in the current memory is the first proven accepted
control-point improvement:

```text
candidate family: branched bend
typed edits: bend control points
parent VLM: 0.4233
child VLM:  0.575
program score: 0.959 retained
result: accepted and selected
```

This proves that the loop can close for one supported edit family. It does not
prove general creative improvement. A future audit must count improvements by
edit type, show the actual graph delta and geometry fingerprint delta, and
compare against unchanged/random-edit baselines.

## Persistence and learning semantics

The result payload writes `accepted_sequences`. The CLI can load prior results
with:

```text
--accepted-seed-from <previous-result.json>
--feedback-from <previous-result.json>
--author-cache-from <cache.json>
--supplemental-author-cache-from <cache.json>
--supplemental-vlm-cache-from <cache.json>
```

The adaptive command can feed artifacts from one round into a later round of
the same command. Across separate invocations, relevant paths still have to be
supplied. Therefore use these terms carefully:

- **durable archive artifact**: true;
- **explicit cross-run reuse**: true;
- **automatic global retrieval**: not proven;
- **online model training**: false;
- **autonomous lifelong learning**: false.

Do not describe cached VLM scores or accepted graph JSON as model fine-tuning.

## Mass-Brain status and correct ownership

ARR already has a fail-open Mass-Brain shadow bridge in
`ARR/backend/design/maas/mass_brain.py`.

It converts ARR seeds to a `mass-brain/v1` envelope containing a `grl/v1`
contract and component-graph domain payloads, requests proposals, accepts only
the executable lane, recompiles those proposals with ARR, and records outcomes
and user feedback. Its artifact explicitly reports
`selection_effect = none_shadow_only`. A service failure does not break ARR.

This is the correct safety boundary:

```text
ARR
  owns executable grammar, compiler, hard gates, QD search and final selection

Mass-Brain
  should own durable cross-project graph/outcome/feedback memory,
  context-aware retrieval, recombination suggestions and experiment evidence

GRL
  should own contract validation, projection, filtering, neighborhood/evidence
  queries and optional GraphLab visualization
```

Mass-Brain should not become a second authority that can promote an uncompiled
or law-invalid graph. Any retrieved or recombined proposal must return to ARR's
compiler and deterministic gates before it can influence the selected set.

### The missing Mass-Brain value loop

A useful next implementation would be:

```text
ARR accepted graph + behavior key + site/program context + scores + evidence
  -> Mass-Brain durable store
  -> project/context query
  -> retrieve diverse, relevant executable parents
  -> optional evidence-backed recombination proposal
  -> ARR compile and hard gates
  -> blind comparison against ARR-only baseline
  -> record outcome and user decision
```

This must be measured. A larger database is not automatically a better design
brain. The test is whether retrieved/recombined parents improve accepted
novelty, quality, capacity and user/VLM preference without reducing legal,
parking, program or geometry validity.

## GRL boundary

GRL is already useful for:

- validating `grl/v1` contracts;
- projecting feature/evidence graphs;
- filtering dense evidence edges;
- querying neighborhoods and evidence;
- displaying lineage with GraphLab.

It does not add creativity merely by visualizing a graph. Creativity can only
increase when its queries or lineage help select better executable parents,
identify missing behavior cells, or explain why an experiment succeeded. Keep
the project-specific parser, component-graph compiler and DB creation in their
own repositories. Use GRL as the shared contract/query layer.

## Why another Grasshopper evolutionary system is probably redundant

The screenshot discussed in the session describes real-time generation,
clustering/behavior analysis, repeated self-exploration and visualization.
Those labels overlap strongly with ARR's existing pipeline. Without source
code, a paper, a genotype definition, objective definitions, mutation rules,
and comparative artifacts, the screenshot is not evidence of an additional
algorithmic capability.

Potentially useful transferable pieces are:

- a better interactive exploration UI;
- real-time population/lineage inspection;
- a behavior-map visualization;
- human steering controls;
- a new executable genotype or mutation family;
- an evaluation method demonstrated to improve architectural outcomes.

Do not integrate a second optimizer based only on the visual resemblance of a
graph UI.

## Current bottleneck: representation, not archive existence

The current archive can only preserve diversity that the executable graph and
compiler can express. The recent memory and visual reviews identify the main
gap as representation breadth:

- graph-native continuous roof/section lofts;
- non-orthogonal sectional folds;
- ground/void fields;
- a second truly distinct continuous topology;
- multiple primary section genotypes;
- visible cluster/field variation that survives compilation and hard gates.

The system also deliberately limits graph/source complexity to avoid LEGO-like
fragmentation. That improves cleanliness but narrows the search space. The
right response is not simply raising node or volume limits. Add a small number
of architecturally meaningful continuous operators and verify their visible
effect.

## Evidence that must remain separate

Do not merge the following claims:

1. **Offline QD/VLM board**: graph authoring, compilation, VLM revision and
   archive selection.
2. **Synchronous legal-design service**: deterministic legal/parking path with
   review/explanation agents.
3. **GRL artifact**: lineage and evidence projection created after selection.
4. **Mass-Brain shadow path**: optional proposals and outcome/feedback bridge,
   with no production selection effect unless explicitly changed and tested.

The named multi-agent review chain is partly explainability/orchestration; it
is not evidence that eight autonomous agents negotiated every candidate.

## Known stale-memory trap

Older sections of `MAAS_MEMORY_INDEX.md` and older handoffs say that
critic-to-geometry revision is missing or that no control-point child was
accepted. Those statements describe earlier versions. The top 2026-07-15
checkpoint and the current code supersede them for the typed offline graph
revision path.

Likewise, artifact filenames v95/v96/v97 may exist beyond the index's v94
representation checkpoint. File existence is not proof that a run is the new
accepted best. A future session must inspect its JSON, PNG, hard-gate status,
and the memory entry that accepts or rejects it.

## Independent audit procedure for the next AI

Do not only summarize this document. Perform these checks:

1. Read `docs/ai-session-memory/MAAS_MEMORY_INDEX.md` and the latest dated
   sections of `MAAS_VISUAL_FAILURE_HANDOFF_20260710.md`.
2. Inspect `graph_archive.py`; record its behavior dimensions, replacement
   semantics and multi-elite frontier behavior.
3. Trace `vlm_a2a.py` from graph loading through compilation, archive,
   critic directive, graph edit, geometry-change rejection, rescore and child
   acceptance.
4. Inspect `adaptive_loop.py` and the CLI arguments to determine whether prior
   accepted graphs are automatic or explicitly supplied.
5. Inspect `mass_brain.py` and its tests; verify shadow status, executable-lane
   compilation, fail-open behavior and outcome/feedback recording.
6. Inspect the newest result JSON and accepted-only PNG. Do not infer success
   from the presence of a filename.
7. Confirm whether legal/parking projection ran for that exact offline result.
8. Search for an automatic global archive registry or DB query used at run
   startup. If found, cite the actual call path; otherwise keep the
   `explicit reuse only` verdict.
9. Count accepted VLM improvements by mutation type and compare parent/child
   geometry fingerprints.
10. State what evidence would falsify each conclusion in this document.

## Copy-paste prompt for another AI session

Give the following prompt to a separate AI session:

```text
이 저장소의 MAAS/Mass-Brain/GRL 구조를 독립적으로 감사해줘. 아래 메모리의
결론을 그대로 믿거나 요약하지 말고 실제 코드와 최신 JSON/PNG 산출물로
반증 가능한지 확인해.

먼저 읽어:
- docs/ai-session-memory/README.md
- docs/ai-session-memory/MAAS_MEMORY_INDEX.md
- docs/ai-session-memory/MAAS_COMPONENT_GRAPH_MAP_ELITES_AUDIT_20260715.md
- docs/ai-session-memory/MAAS_AGENT_COLLABORATION_FLOW_20260714.md
- docs/ai-session-memory/MAAS_VISUAL_FAILURE_HANDOFF_20260710.md 의 최신 날짜 섹션

반드시 직접 확인할 코드:
- ARR/backend/design/maas/program_massing/graph_archive.py
- ARR/backend/design/maas/program_massing/vlm_a2a.py
- ARR/backend/design/maas/program_massing/adaptive_loop.py
- ARR/backend/design/maas/agents/orchestrator/generative_loop.py
- ARR/backend/design/maas/agents/llm_architect_agent/graph_revision.py
- ARR/backend/design/maas/mass_brain.py
- ARR/backend/design/test_mass_brain.py
- scripts/run_neighborhood_vlm_a2a.py

다음 질문에 각각 `확인됨 / 부분 확인 / 확인 안 됨 / 반증됨`으로 답하고,
파일과 줄 번호 또는 JSON 필드를 근거로 제시해:

1. 현재 ARR이 executable component graph를 genotype으로 쓰는가?
2. GraphBehaviorArchive가 실제 실행 경로에서 쓰이며 behavior cell 교체를
   수행하는가?
3. 이것을 canonical MAP-Elites라고 불러도 되는가, 아니면 constrained
   MAP-Elites-like hybrid가 더 정확한가?
4. VLM critic이 typed graph edit를 만들고, child를 재컴파일하고, 실제
   geometry 변화와 점수 개선을 검사한 뒤 archive에 반영하는가?
5. v88의 `0.4233 -> 0.575`, program score `0.959` accepted child 근거가
   최신 artifact에 실제로 존재하는가?
6. accepted_sequences가 다음 실행에서 자동 검색되는가, 아니면
   --accepted-seed-from 등의 명시적 경로가 필요한가?
7. 자동 전역 archive DB 또는 online learning이라고 부를 코드 경로가 있는가?
8. 최신 offline board에서 법규와 주차 projection이 실제 실행됐는가?
9. GRL은 generator/optimizer인가, 아니면 contract/query/evidence viewer인가?
10. Mass-Brain shadow proposal이 현재 final selection에 영향을 주는가?
11. Mass-Brain이 기존 ARR archive와 중복되지 않으면서 실제로 창의성을
    높이려면 어떤 최소 폐루프가 필요한가?
12. 현재 가장 큰 병목은 optimizer 부재인가, graph/compiler 표현력인가?

추가로 docs/playwright/design-route-live-verify 아래의 가장 최신 v95 이상
산출물을 확인해. 파일이 존재한다는 이유만으로 best라고 하지 말고 JSON의
accepted count, hard-gate 상태, language/topology coverage, legal/parking 상태,
critic child acceptance와 PNG의 실제 시각적 차이를 확인해.

마지막에는 다음 형식으로 보고해:
- 최종 판정
- 코드로 확인된 사실
- 메모리와 코드가 충돌하는 부분
- 과장하면 안 되는 주장
- Mass-Brain을 붙였을 때의 측정 가능한 이득 가설
- 그 가설을 검증할 ARR-only 대 ARR+Mass-Brain A/B 실험
- 다음 구현 3개(중복 optimizer 추가는 근거가 있을 때만)

가능하면 테스트를 실행하되 코드는 수정하지 마. 수정이 필요하다고 판단하면
먼저 수정 제안과 기대 효과만 보고해.
```

## Recommended A/B test before deeper integration

Compare the same site/program/reference seed under fixed budgets:

| Arm | Parent source | Generation/evaluation |
|---|---|---|
| A: ARR-only | current fresh + explicit local accepted seeds | existing compiler, gates, VLM and selector |
| B: ARR + Mass-Brain retrieval | same budget, with context-retrieved historical executable parents | exactly the same compiler, gates, VLM and selector |
| C: ARR + Mass-Brain recombination | same budget, retrieved parents plus evidence-backed recombinations | exactly the same compiler, gates, VLM and selector |

Report at minimum:

- compile-pass rate;
- legal and parking mass-stage pass, when actually run;
- accepted archive size;
- occupied behavior cells;
- pose-invariant and silhouette uniqueness;
- accepted VLM improvement rate by edit family;
- program/capacity pass;
- blind human preference;
- result diversity at equal evaluation cost;
- retrieval/recombination contribution lineage.

Mass-Brain is useful only if B or C improves these outcomes at equal budget,
not merely because it stores more nodes or renders a larger graph.

## Safe next implementation priorities

1. Persist ARR accepted executable graphs, behavior keys, context, outcomes and
   graph/geometry fingerprints into Mass-Brain with idempotent IDs.
2. Add context-aware diverse parent retrieval, but keep it shadow-only until
   an equal-budget A/B test demonstrates benefit.
3. Add missing high-value graph/compiler genotypes and typed mutations,
   especially continuous section/roof and non-orthogonal field operations.
4. Add automatic experiment evidence: parent/child graph diff, geometry diff,
   gate result, VLM delta, selection result and user feedback.
5. Use GRL queries and GraphLab to inspect this evidence; do not let UI state
   become optimization truth.

## Final one-sentence handoff

ARR already has the core component-graph constrained MAP-Elites/VLM revision
engine; the next credible gain is broader executable representation plus
Mass-Brain-backed automatic cross-project elite retrieval and measured outcome
learning, while GRL remains the validated evidence/query/lineage layer.
