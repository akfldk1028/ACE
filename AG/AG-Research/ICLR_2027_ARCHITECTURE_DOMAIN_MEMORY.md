# ICLR 2027 Architecture-Domain Memory

## AUTHORITATIVE RESEARCH-DIRECTION UPDATE -- 2026-08-20

This section supersedes the older CATS-centered research direction below. The historical body is retained as an audit trail and must not be treated as the current paper plan.

### Current scientific status

- The completed development pipeline is technically verified, but the scientific method gate is negative.
- Frozen CATS results: median token reduction `0.0`; unsafe stops `2`; mean-quality non-inferiority lower bound `-0.012222`; empirical coverage `0.988889`.
- Exact blockers remain `development_gate_failed` and `pilot_gate_failed`; `held_out_access_allowed=false`.
- Authoritative development-gate file SHA-256: `e4f64639991b617955b4e2f2821a46205e0d7dd5f9b79aef4fd883b729c565b5`.
- Latest locked candidate SHA-256: `c4a16171c5328389185a1995ed1881bdf893a4afb788ac17cf405165918c7a8b`.
- Latest execution-memory SHA-256: `83f6ef0fcbebabb40daa810bb382c5366d8a282452ebb3559e2eab8c466530ce`.
- CATS is therefore a negative baseline and motivation. Do not revive it as the main contribution and do not claim that safe early termination is impossible.

### One paper thesis -- causal-mechanism amendment

Working title:

> **Hard Is Not Enough: Causal Obligation--Capability Alignment in Verifiable Multi-Agent Reasoning**

Central claim to test:

> **Task difficulty predicts whether escalation may be needed; independently measured residual-obligation--capability alignment causally shifts and predicts which collaboration pays.**

Memorable conclusion:

> **Hard is not enough. Collaboration pays when the remaining obligation matches a real capability advantage.**

Control principle:

> **Topology is not the control variable; residual obligations are.**

Operational form:

> **Multi-agent termination is residual-work allocation, not confidence estimation.**

This is not yet a result. It remains a falsifiable hypothesis until a randomized capability-swap study establishes the mechanism on disjoint data and a non-gold controller passes its locked gate. OACS is the operational consequence of the mechanism, not the novelty claim by itself.

The earlier same-branch definition of capability effect was circular: using focal branch payoff to estimate expected closure and then claiming expected closure predicts payoff would only restate the outcome. The authoritative design therefore requires a capability matrix estimated and frozen on disjoint capability-audit sites before any focal branch outcome is opened. The controller must receive opaque action slots with frozen capability profiles, never semantic `law -> ASK_LAW` lookup labels.

For a runtime action slot (a), use the implementable action-specific score

\[
\Gamma_a(z)=\sum_i w_i p_i(z)
\left(\mu^{\mathrm{audit}}_{ia}-\mu^{\mathrm{audit}}_{i,\mathrm{solo}}\right)
-\lambda\Delta c_a,
\qquad
\Gamma(z)=\max_a\Gamma_a(z).
\]

Do not maximize a different specialist independently for every obligation while paying coordination cost once. The entire selected action must be executable as one frozen branch.

The paper evidence must form one chain rather than three disconnected contributions: (T0) scalar-state aliasing implies unavoidable action regret; (E1) difficulty improves escalation prediction; (E2) randomized capability swaps identify the causal alignment effect; (E3) alignment reduces action regret beyond an equal-information router; and only then (E4) fresh sequential OACS improves the cost--quality frontier. Architecture supplies the main externally grounded intervention, and one independently frozen ontology supplies decisive replication.

Round-3 adversarial verdict is **REVISE, not yet a result**. The primary E2 outcome is blind terminal obligation closure/quality under cost-matched high-versus-low actual capability bundles; cost-adjusted utility is secondary at this layer. E3 is the decisive method test: a positive E2 with no action-regret improvement over a truly equal-information generic router is only a bundle-effect study, not an OACS/ICLR-main method contribution. E4 must then use fresh, non-stitched sequential rollouts. The complete packet is the causal treatment; do not claim an intrinsic agent trait or a causal effect of the numeric alignment score itself.

The preferred second ontology is **JCI-Repair-v1**, a Java CI-contract repair setting frozen before architecture confirmatory outcomes. Public obligations come mechanically from functional test groups, compile/API contracts, whole-project assurance rules, and only genuinely declared resource budgets. Opaque complete capability packets provide test localization, API/type analysis, security/static analysis, or performance/resource profiling; one common synthesizer alone writes patches. Gold patches, target tests/warnings, modified-file lists, fixed revisions, and hidden evaluator feedback remain evaluator-only. Use project-disjoint, hash-pinned Defects4J/Vul4J pools; the minimum mechanism pilot is 80 eligible prefixes from at least eight repositories, four packets by three repeats. Freeze and test directional E1 transfer as well as the primary E2/E3 replication. If at least 20 genuine resource-obligation prefixes across three repositories do not exist, kill the four-packet claim rather than manufacture balance. Evidence synthesis is not the fallback causal domain because its completeness oracle is open-world.

### Current method hypothesis: OACS

OACS means **Obligation-Aware Coordination and Stopping**.

- State: typed residual obligations plus public evidence, prior messages, cost, and admissibility status.
- Architecture obligation families: site/evidence, law, parking, program, and geometry.
- Canonical execution-log actions: `STOP`, `SOLO_SYNTHESIS`, `ASK_LAW`, `ASK_PARKING`, `ASK_PROGRAM`, `ASK_GEOMETRY`.
- Controller actions: opaque runtime slot IDs bound to independently audited capability profiles. Canonical semantic action names are hidden from the policy and may not be used as features.
- Action value: expected reduction in weighted residual-obligation risk minus measured action cost.
- Entry: take the solo path when no specialist has positive conservative residual-closure value at the initial state.
- Routing: invoke the specialist with the greatest positive conservative residual-closure value.
- Exit: stop only when the hard terminal gate passes and no available action has positive conservative value.

Named topologies are baselines and realized action sequences, not the paper's primary control variable.

### Why architecture is the flagship domain

Architecture is not a decorative application or one-third of a three-domain paper. It is the primary causal testbed because obligations and unsafe omissions are independently auditable:

- law: use, FAR/BCR, height, setbacks, and required legal evidence;
- parking: count, supply, dimensions, and placement;
- program: area capacity, adjacency, circulation, and completeness;
- geometry: compile/normality, measured quantities, and geometric consistency;
- site/evidence: site identity, provenance, and packet completeness.

The endpoint set includes terminal issue precision/recall/F1, exact issue agreement, false-clear and unsafe-stop counts, admissibility-gated verdict, tokens, turns, latency, cost, and unnecessary specialist calls, but they are not jointly primary. E2's primary is blind terminal obligation closure/quality for the frozen high-minus-low complete-packet contrast; its cost-adjusted utility and continuous interaction are secondary. E3's primary is action regret. Complete processed tokens become primary only for constrained fresh E4, with the three terminal-quality non-inferiority endpoints reported separately.

For new experiments, the primary resource measure is complete provider-reported processed tokens across agent, selector/router, verifier, synthesis, and failed-retry calls. Input/cache/output components must be counted exactly once. Historical CATS `visible_agent_tokens` exclude important compute classes and must never be presented as total compute.

A baseline is eligible for the main efficiency comparison only with zero unsafe stops and separate `0.02` non-inferiority margins for blocking-issue F1, missing-evidence F1, and decision accuracy. Do not hide these constraints inside the legacy weighted quality composite.

The case/site is the inferential unit. Prefixes and repeated trajectories are not independent samples. Confirmatory uncertainty must be clustered by site/case or modeled hierarchically.

### Novelty boundary

Do not claim novelty for any of the following individually:

- adaptive multi-agent routing or an MDP formulation;
- single-versus-multi-agent selection;
- verification-aware planning;
- conformal early stopping or risk-controlled compute;
- adaptive stochastic set cover.

The novelty target is a measurable obligation--specialist alignment account of collaboration payoff; the explicit residual-obligation state that unifies entry, specialist choice, and exit; a difficulty-versus-alignment and state-aliasing analysis; an architecture benchmark with typed obligations and specialist interventions; and a measured cost-risk frontier improvement over strong 2025--2026 baselines.

GraphPlanner, VeriMAP, RIRS/Talk to Right Specialists, Verified Multi-Agent Orchestration, recent Cost-Aware Protocol Routing, MasRouter/BiCSRouter, Conformal Thinking, CATS, fixed topologies, all-specialists, and an independent router-then-stopper cascade must be addressed or approximated as baselines. If typed residual-obligation state does not add value beyond task difficulty, scalar confidence, and these methods, the paper thesis fails.

### Non-negotiable anti-leakage boundary

The live controller may use only public evidence, prior agent outputs, public task specifications, provenance/schema checks, and declared admissibility signals. It may not use mutation family, gold issue codes, expected terminal decision, hidden evaluator output, or gold-derived obligation status.

Gold may label branch outcomes offline only after outputs and usage are frozen. A hard validator that tells the controller which hidden obligation is missing invalidates the experiment.

Safety claims are limited to the declared verifier-covered obligation universe. Never claim universal safety against unknown or omitted obligations.

### Immediate kill-gated next step

Before building or training OACS, run a development-only randomized capability-swap mechanism pilot. No held-out/OOD access is authorized. First freeze a capability matrix on sites/cases disjoint from the focal pilot. Then, at each predeclared focal prefix, collect directly observed terminal branches under opaque action IDs, randomized surface-name permutations, and randomized complete specialist packet/tool bindings. `STOP` terminates directly, `SOLO_SYNTHESIS` runs once, and each specialist branch runs exactly one frozen capability packet followed by the identical bounded synthesis wrapper. Repeat stochastic branches and estimate expected value with uncertainty; never take a single lucky draw as an oracle and never splice transitions.

The E2 primary is the site-clustered finite-prefix mean contrast in blind terminal obligation closure/quality between pre-outcome, cost-matched high- and low-alignment directly executed complete packet sets, with audit-profile provenance frozen on disjoint sites. Complete cost-adjusted utility and a within-prefix centered continuous alignment interaction are jointly reported secondary specifications and cannot substitute for E2. A surface-name permutation should leave the effect essentially invariant; swapping the actual capability behind the advertised profile should remove a substantial part of the advantage. The primary E3 equal-information router receives the exact raw public packet/transcript, numeric residual serialization, complete frozen capability table, opaque binding/cards, costs, admissibility, examples, outcome-free splits, learner class/capacity, and tuning budget. No-obligation/no-profile variants are ablations, not E3 comparators. Faithful Cost-Aware Routing, RIRS, VMAO, and VeriMAP implementations are mandatory wherever their official interfaces permit faithful execution.

Current data are insufficient for a positive causal gate: five sites/30 cases can support only a negative-oriented manipulation smoke. The structural Gate-A planning floor is eight disjoint Architecture sites/64 typed target units. Exactly 1,024 terminal records and 1,728 no-retry branch-generation calls are valid only for a signed candidate with exactly one selected prefix per target and a complete isolation/reuse-equivalence proof. The previously stated 9,216-record/13,824-call fallback has no reviewed typed derivation and is withdrawn. Without the reuse proof, the alternative candidate is `NO-GO` until every distinct assignment, terminal, call, protocol operation, retry, cost, and dependency row is explicitly enumerated. These are conditional structural counts, not call authorization, powered sample sizes, or scientific results; prospective clustered power analysis may require more sites or targets.

Proceed only if the obligation oracle satisfies every frozen feasibility condition:

1. receipt-bound E1 `LogLoss(H|B)-LogLoss(H|B,D)` has a positive one-sided site-clustered 90% development lower bound and satisfies the frozen calibration criterion;
2. the frozen E2 high-minus-low blind-closure contrast has a positive one-sided site-clustered 90% development lower bound, standardized effect at least `0.20`, appears in at least three specialist families, and no site contributes more than half;
3. surface-name permutation changes policy performance by at most `0.02`, while actual capability misbinding removes at least half of the alignment advantage;
4. E3 action regret falls at least `0.20` versus difficulty/confidence and at least `0.10` versus the full-parity equal-information router, each with its own positive one-sided site-clustered 90% development lower bound, and validator/controller leakage audits are clean;
5. the uncertainty-adjusted policy opportunity implies at least `0.15` end-to-end processed-token reduction with lower bound at least `0.10`, subject to separate `0.02` non-inferiority bounds for blocking-issue F1, missing-evidence F1, and decision accuracy;
6. repeated branches, complete processed-token accounting, disjoint capability estimation, and site/case-clustered inference are all present;
7. JCI-Repair-v1's ontology, packets, evaluator, public/hidden boundary, split manifests, and E2/E3 contrasts are frozen before architecture confirmatory outcomes; its later replication is required before a general cross-domain claim, not to reinterpret Gate A;
8. no universal or `<1%` safety claim is made from the current 30 cases. Such a claim requires a separately powered, predeclared sample with enough independent cases and sites; zero observed events alone is reported descriptively until then.

Failure of the causal mechanism gate stops OACS development and keeps held-out access denied. A positive one-decision mechanism pilot is necessary but not sufficient and is not an end-to-end OACS result. The deployable non-gold controller must be evaluated on fresh sequential development rollouts and independently pass the frozen cost and quality gates before method lock. Safety language remains limited to observed unsafe omissions in the declared obligation universe unless a separate risk study is adequately powered.

The 90% intervals above are development go/no-go tools only. Locked confirmatory E1/E2/E3 and fresh E4 require predeclared site-clustered or hierarchical 95% intervals: E1 and E2 lower bounds above zero; E3's `0.20` and `0.10` point thresholds with separate lower bounds above zero; E4's `0.15` token-saving point estimate with lower bound at least `0.10`, `0.10` versus separated routing with lower bound above zero, and all three quality non-inferiority lower bounds above `-0.02`.

The exact paper-level kill chain is binding: E1 failure removes the difficulty headline; E2 failure kills the causal mechanism; E2 positive but E3 null kills the OACS method claim; E3 positive but fresh E4 null kills the deployable frontier claim; failure to reproduce E2/E3 in frozen JCI-Repair-v1 kills the cross-domain/general mechanism claim. CATS and safe early stopping remain negative motivation/baselines and are never counted as a paper contribution.

### Authoritative design and plan

- Design: `docs/superpowers/specs/2026-08-20-obligation-aware-coordination-design.md`
- Execution plan: `docs/superpowers/plans/2026-08-20-obligation-aware-coordination.md`

The next implementation session must begin with Stage 0 read-only inventory and cost estimation. It must not jump directly to model calls, controller training, held-out access, or manuscript claim rewriting.

Current official ICLR 2027 pages checked 2026-08-20 list abstract deadline 2026-09-18 AOE and paper deadline 2026-09-25 AOE. Gate A must be positive by Sep 1 and the learned end-to-end Gate B by Sep 7; otherwise do not force OACS into an ICLR main-paper claim. The ICLR 2027 mandatory AI-use disclosure must accurately cover AI assistance in hypothesis formation, literature analysis, methodology, implementation, interpretation, translation, and writing.

## Implementation checkpoint — 2026-08-18

Implemented locally in `AG/AG-Research`:

- modular `iclr2027` schemas, ARR adapter, dataset builder, five fault families, independent validators, review-state parser, architecture metrics, architecture role/topology factory, Exp08 runner, and pilot gate;
- public/gold separation, recursively immutable evidence packets, site/law/parking/program/geometry evidence, exact terminal issue agreement, and admissibility-gated verdict scoring;
- frozen site registry plus four-bundle split manifest. Normal runs load only files bound by the verified manifest; `--cases-dir` is fixture-only with `--allow-unfrozen --dry-run`;
- atomic per-run transaction files, automatic JSONL/CSV reconstruction after a torn write, full resume identity, bounded retry lineage, dirty-source code identity, and paid-run/cost/date confirmation gates;
- paper-claim audit rules for unfinished human evaluation, unequal Exp07 repeats, unsupported priority claims, and ambiguous “14 topologies” wording.

Verified locally at this checkpoint: the ICLR-specific unit suite passes. The exact fresh count and legacy integration evidence belong in the handoff message, not as a permanent scientific result.

Not executed and therefore not a result claim:

- selection and live ARR generation for five new held-out PNU sites;
- the complete frozen 12-case development and 30-case test bundles;
- any paid one-case smoke run or the 180-run pilot;
- CATS training/replay, the 1,260-run primary matrix, cross-model runs, statistical analysis, or a submission-ready paper.

Next hard gate: collect the real development artifacts, freeze all four expected bundles, price the pilot, run one paid smoke case, then run the 180-run pilot only if the prompt/gold audit and budget/date checks pass.

Execution audit (2026-08-18): the default Claude path is Claude Max OAuth through `ClaudeCLIChatCompletionClient`, so marginal API invoice cost is conditionally USD 0.00 rather than a metered Anthropic API charge. This does not make the pilot operationally free: selector calls and retries can produce thousands of completions, the SDK has no strict timeout, and subscription quota can interrupt the run. Existing Exp01/Exp07 timing yields a historical planning proxy of about 12.48 hours without retries and 37.44 hours when mechanically tripled; neither is a guaranteed upper bound. Dry-run, smoke, and pilot must use separate checkpoint directories because run manifests are intentionally incompatible across different matrices.

> 최종 방향 기록 · 2026-08-18 · 다음 세션에서도 이 범위를 기준으로 작업한다.

## 확정된 논문 방향

기존 연구 질문은 유지한다.

> **When Should Multi-Agent Teams Stop?**

논문은 세 부분으로 구성한다.

1. 기존 Exp01–Exp07의 topology별 종료·비용·품질 분석
2. Exp08: 건축 hard-constraint 도메인 전이 실험
3. Exp09: 최소한의 학습형 `STOP/CONTINUE` 방법인 CATS

CATS의 작업명은 **Constraint-Aware Team Stopping**이다. 미래에 유의미한 품질 개선이 남았는지를 예측하고, 궤적 단위 conformal calibration으로 조기 종료 위험을 통제한다. 건축에서는 ARR의 독립 hard gate가 모두 충족된 상태에서만 STOP을 허용한다.

## 하지 않는 것

다음은 이번 ICLR 2027 제출 범위가 아니다.

- `STOP / CONTINUE / HANDOFF / REPAIR / REGENERATE` 5-action RL controller
- GraphPlanner, CARD, ZIP-RC를 한꺼번에 합친 새 orchestration framework
- ARR 전체를 AG 프레임워크로 다시 구현하는 작업
- 미학적 우수성이나 “더 좋은 건축”을 주 결과로 주장하는 것

이 방향은 별도 후속 연구로만 남긴다.

## 건축 도메인의 정확한 역할

ARR가 동일한 대지·프로그램에 대해 다음 증거를 생성하고 검증한다.

- geometry compile 및 형상 gate
- 법규·BCR·FAR·높이·용도 증거
- 주차 요구량과 배치 증거
- 프로그램·수용량·공간 구성 증거
- 실행 identity와 geometry/program hash

AG의 각 topology는 같은 frozen evidence packet을 받아 설계 검토와 종료 결정을 수행한다. 따라서 비교 대상의 설계 원본은 동일하고, topology와 종료 정책의 효과만 분리한다. 이 실험은 MASS 하나가 아니라 법규·주차·프로그램·형상을 포함한 건축 설계 검토 루프다.

## 실험 단위

- 총 시스템: **14개 = 13 multi-agent topologies + 1 solo baseline**
- 프로그램: 근린생활시설, 체육관, 문화시설
- 개발 세트: 기존에 반복 사용한 2 PNU × 3 프로그램 × 2 상태 = 12 cases
- 고정 테스트: 저장소에 등장하지 않은 신규 5 PNU × 3 프로그램 × 2 상태 = 30 cases
- 개발과 테스트에 같은 PNU를 재사용하지 않는다.
- 개발 PNU는 `1168011800104170004`, `1168011800104670003`으로 고정한다. 최종 5개는 live boundary/law/parking 조회가 성공하고 2026-08-18 저장소 snapshot에 PNU 문자열이 없는 대지로 2026-08-21까지 동결한다. 불가능하면 기존 PNU를 evaluation-only split으로 사용하되 system-level OOD 주장을 삭제한다.

예정 실행 수:

- pilot: 5 patterns × 12 cases × 3 repeats = 180
- primary: 14 systems × 30 cases × 3 repeats = 1,260
- cross-model: 5 patterns × 30 cases × 2 repeats = 300
- canonical ARR fixed-flow baseline: 30 deterministic cases × 1 = 30
- 총 신규 실행: **1,770**

여러 종료 정책은 동일한 full trajectory를 offline replay하므로 정책 수만큼 LLM을 다시 호출하지 않는다.

## CATS의 핵심 정의

각 turn 상태 `x_t`에서 다음 label을 만든다.

`y_t = 1` iff `max_{k>t} Q_k - Q_t > epsilon`

즉 `y_t=1`은 계속 진행하면 유의미한 품질 개선이 남았다는 뜻이다. 모델 입력에는 미래 quality와 judge score를 넣지 않는다. turn 위치, topology, agent 수, 누적 token, 최근 변화, 반복/semantic convergence, 그리고 건축 validator 상태만 사용한다.

STOP 조건은 모두 충족해야 한다.

1. conformal prediction set에서 `y=1`이 제외됨
2. 건축 hard-stop admissibility가 참임
3. 조건이 연속 2개 agent turn에서 유지됨

## 주 평가 지표와 성공 기준

주 평가 단위는 case/trajectory이며, 동일 case·seed 내 paired 비교를 한다.

- stopped quality 및 full-trajectory peak 대비 quality loss
- token·latency 절감
- premature stop, overshoot turn, oracle regret
- hard-constraint unsafe stop
- calibration coverage, Brier score, ECE
- quality–cost Pareto frontier

사전 성공 기준:

- `ΔQ = Q_stop - Q_full`의 평균에 대한 95% CI 하한이 `-0.02`보다 큼
- median token reduction이 최소 `20%`
- 건축 frozen test에서 recommended policy의 관측 unsafe stop이 0건
- zero-event 결과도 Wilson/cluster-bootstrap CI와 함께 보고하며 “위험 <1%”처럼 표본이 뒷받침하지 않는 주장은 하지 않음

## 논문 정리 원칙

- 본문 기여는 세 개만 유지한다: 대규모 실증, CATS, 건축 검증.
- 기존 39개 finding은 appendix로 이동한다.
- Exp05를 “학습된 estimator”라고 한 문구를 삭제하고 실제 어휘 기반 ΔU heuristic으로 정정한다.
- `13 patterns` 표현을 `13 multi-agent topologies + solo`로 통일한다.
- 모델이 다른 token 수를 직접 비교한 초록 문구를 같은 모델 비교로 고친다.
- 비어 있는 human-evaluation sheet를 근거로 한 주장을 삭제한다.
- 건축 결과는 미학이 아니라 독립 실행 validator와 종료 안전성으로 평가한다.

## 마감 판단

현재 ARR loop와 validator가 이미 구현돼 있어 기술 구현 위험은 중간이다. 가장 큰 위험은 코드가 아니라 7개 PNU의 누수 없는 분할, 1,770회 실행 비용·오류율, 통계 분석, 9페이지 본문 압축이다. 아래 gate를 통과하지 못하면 실험 범위를 더 늘리지 않는다.

- pilot parse success ≥ 95%
- pilot run error < 5%
- 개발 세트에 safe/unsafe 상태가 각각 최소 30%
- CATS가 개발 세트에서 quality non-inferiority와 ≥ 15% token saving의 초기 신호를 보임
- pilot으로 산정한 전체 API 비용과 시간이 제출 일정 안에 들어옴

세부 설계와 실행 순서는 `ICLR_2027_ACCEPTANCE_DESIGN.md`와 `ICLR_2027_ACCEPTANCE_PLAN.md`를 따른다.

## Current execution status -- Task 3A closure and Task 4 boundary (append-only, 2026-08-20)

- This is an execution-memory update, not a scientific or review approval. Novelty retains responsibility for semantic non-regression review.
- Task 3A's authenticated current-state Gate 0 artifact is approved as an inventory outcome and reports only `data_collection_required`: 5 sites, 30 cases, 450 historical runs, 1,524 prefixes, and standardized OACS branch coverage `0/6`. Model calls, controller calls, refits, and held-out/OOD or restricted child-body accesses remain zero. It does not provide a positive causal, safety, acceptance, or publication claim.
- The canonical LF artifacts are inventory SHA-256 `c9b31e54d12793f6e94425f9c38f6947692ab5d1a8bcda530baa483d6ee0c6ac` (self `f111cdee1e255607dc59f13280bed43d86cd3601e6db89b39056fa7a8526e0ad`) and receipt SHA-256 `1a2e400cba95021336ef58ba4ae929b4ef4965596d5c85c6d79735cff209e55c` (self `fd1ae7af8f0fe9be76ce6303c923bbd23d4704eb7a6b9a6f157cee61c25ac010`); their source-map SHA-256 is `cf58572aeeeaec4295763867aae6409232cde2330f5f2842256e8c76a863bad7`.
- Material artifact and stabilized publication reviews have no Critical or Important finding. The publication review retains one documented Minor operational boundary: POSIX same-UID filesystem authority is not process isolation; a source output directory must not grant an untrusted same-UID actor rename authority. That actor still cannot make a verifying pair or cause the process to publish outside the retained directory under the reviewed contract.
- The next authorized step is Task 4 Phase 4A, synthetic-only. Task 4 Phase 4B source-mode execution and publication are hard-blocked until the separately versioned two-phase Task 3 trust-root pin exists and is independently re-reviewed. Task 3A itself authorizes no calls or data collection.
- The single architecture-first thesis and E2--E3--E4 kill chain are unchanged: E2 failure kills the causal mechanism, positive E2 with null E3 kills the OACS method claim, and positive E3 with null fresh E4 kills the deployable-frontier claim. No positive result or acceptance claim follows from the current status.

## Current research lock -- obligation-aware coordination (append-only, 2026-08-20)

### One paper-level conclusion

The ICLR-main candidate is not a safe-stopping paper and not a generic multi-agent routing paper. Its single testable conclusion is:

> Multi-agent collaboration creates value when the unresolved obligations at a decision point are conditionally complementary to the complete capability bundle that is actually executed; an obligation-aware coordination policy is useful only if it exploits that structure beyond an equal-information raw router.

Architecture is the flagship domain. JCI-Repair-v1 is a separately frozen ontology and replication domain, not pooled extra power. CATS/safe early stopping is motivation or a baseline only. E1, the benchmark scaffolding, and the synthetic Phase-A instrument are support for the one mechanism-plus-policy contribution, not separate headline contributions.

### Confirmatory chain and claim gates

1. **E1 (predictive support only):** test whether difficulty/confidence predicts complete-action escalation labels under site-held-out Phase-B evaluation. E1 is noncausal and nonprimary. A null E1 removes the difficulty headline and blocks the present E4 route, but does not by itself negate a separately valid E2.
2. **E2 (primary mechanism):** randomize and verify actually executed high-versus-low complete capability bundles within the predeclared shared target menu and estimate the site-clustered effect modification after residual-absent, global-strength, and uniform-admissible controls. A nonpositive, nonestimable, unsupported, or noncompliant E2 in either Architecture or JCI kills the mechanism and OACS thesis.
3. **E3 (policy consequence):** compare OACS with a full-parity raw router using the same canonical parent information, complete action menu, costs, admissibility, examples, split, learner capacity, tuning opportunity, and tie rule. The secondary policy family contains 22 exact readiness-gated methods. A retrospective oracle is a separate post-outcome descriptive upper bound, never a deployable policy. Positive E2 with null or parity-invalid E3 reduces the paper to a bundle-effect study.
4. **E4 (fresh sequential deployment test):** run only after the required E1/E2/E3 gates. Null E4 kills deployable-frontier language but need not erase an offline mechanism/policy result.
5. **Cross-domain replication:** Architecture and JCI E2/E3 must each pass separately. Effects are not pooled across ontologies to manufacture significance.

### Frozen synthetic Phase-A instrument status

Task 5 v2 is a zero-call scientific instrument, not an empirical result. It verifies canonical schemas, typed reference closure, predeclared ownership/reuse, exact actual-byte parity replay, baseline readiness/cardinality, and fail-closed Phase-B boundaries. It authenticates no real source/version, timing, no-outcome access, learner fit, baseline fidelity, process consumption, causal effect, safety, pass, or acceptance claim.

Final authorities and reviews:

- Task 5 brief SHA-256 `8d2f27d2fb9e6901d7bfed90407a25f8c714d23fe9d2f511a469494e272054ee`.
- Identification/analysis plan SHA-256 `2809048fa71d0f2458db13f7590c61f0f28674f2195c3d8690a45193df517299`.
- Final authority review `task-5-brief-review.md` SHA-256 `8d98a17ee57b1a254d4f651d74b44b696ec022e3822daea1b8a3f25036060cc8`.
- Task 3 implementation review `task-5-v2-task-3-review.md` SHA-256 `58cd8abd389f4cf839b7cb8a3211e962d616d72306ab976e6f795c8f40cf93ab`.
- Task 4 implementation review `task-5-v2-task-4-review.md` SHA-256 `f8fd72c9ff51f1d1e3d0aeaea0a97a80a4e1777f0b110e936c5490d0bc6d711d`.
- Final Task 5 report `task-5-report.md` SHA-256 `b8b8475ab667db65eddc1966f864668c2ee8feb66dacf797e72d2f8cfe6153ef`.

Frozen repository bytes:

- `iclr2027/obligation_oracle.py`: `84c71043d9fcbd5905332af3a1ea2b05ef08c5b3f765d30699d8d855f8212804`.
- `iclr2027/obligation_escalation.py`: `c66e3349503aa02774689314235d9e3550953b32b3808d5dfd4619c222eca9c8`.
- `tests/test_iclr2027_obligation_oracle.py`: `1f169f9d9e66dce94e3bd21da0fb17f1382a45030325593fd12cd0c402e680fc`.
- `tests/test_iclr2027_obligation_escalation.py`: `856f5101ed25f92de51b57a1a3fe6f0a67f4a85d6ffb38f3a604441db5c5fbd9`.
- Oracle CLI: `37b20ed8edf189e380b74dfcf8b246806fac11a179b5f33b7bff8dc4e488791d`.
- Escalation CLI: `a0dd7545b3280489d4407f9d4dbba1f7dc83dc27646ecb77b41998bcf5a498a7`.

Verification on the frozen bytes: focused `101/101`; adjacent six-module `223/223`; full safe discovery `656` passed, `9` platform skips, zero failures/errors; Ruff, six-file AST parsing, in-memory compile, two CLI help probes, eight exact `NEEDS_CONTEXT` flag probes, and three before-I/O observer tests all passed. Restricted-artifact reads and real model/controller/evaluator/baseline calls were zero.

### Data sufficiency and cost lock

The current authenticated inventory remains only 5 sites, 30 cases, 450 historical runs, 1,524 prefixes, and standardized OACS branch coverage `0/6`. It cannot support the frozen positive site-clustered gate and is only a negative-oriented smoke/finite-roster diagnostic.

Before any paid confirmatory call, freeze an externally receipt-bound `architecture_e1_e2_e3_precall_design_lock`. The structural development floor is 8 disjoint sites and 64 case-family target units: audit 3 sites/24 units plus focal 5 sites/40 units. With six actions (STOP once and five non-STOP actions at three seeds), exactly one selected prefix per target, and proven execution isolation/reuse equivalence, this is 1,024 terminal records and 1,728 no-retry branch-generation calls (648 audit plus 1,080 focal). Each additional selected target-prefix adds 16 terminals and 27 branch-generation calls without adding a power unit. If reuse equivalence is not proven, there is no authorized numeric fallback: the alternative treatment plan must be completely enumerated before any count or budget exists. The old 13,824-call figure is unbound and must not be used. These are conditional structural floors, not powered final sample sizes.

The pre-call lock must freeze the authenticated site/unit roster, audit/focal split, present/absent controls and support census, isolation verdict, synthetic variance/ICC/covariance and MDE/power grids, leave-one-site-out support, alpha/CI algorithms, substantive margins, target power, attrition ceiling, backend/model IDs, token ceilings, retries, tool limits, official rate snapshot, worst-case cost/time, randomization/inference seeds, and a PASS/NO-GO decision. No numeric budget is defensible until those manifests and rates are bound. Failed retries remain in the cost sum.

The zero-call Task 6 authority is now frozen at brief SHA-256 `364b89d3ca1726177ecf0b26f5258d55dcc765f6b38c3f9665666d811f0ba1e2` and companion-analysis SHA-256 `428f2bb21b13e1ca2d23c6bd4bb8a6ddb483aba31aef20ae06e7ab6603a0127c`. Its final dual review is `APPROVED` with Critical/Important/Minor `0/0/0`; the review SHA-256 is `2898d1e5c5f4f1e5238bfbd651c3aee5ecb236fb97201c67e22dbbfcd4505962`. This approval authorizes only a synthetic validator and adversarial TDD. It does not authorize source access, simulation execution, paid calls, an official PASS, or an empirical paper claim. The present decision remains deterministic `NO-GO`/`NEEDS_CONTEXT`.

### Exact next sequence

1. Create and independently review the external source/version trust anchor and same-handle Phase-B authority; until then all real source modes remain `NEEDS_CONTEXT`.
2. Build the zero-call pre-call design lock and run randomization/power/cost simulations over conservative variance and missingness grids. Do not invent empirical variances from the zero-branch inventory.
3. If the lock is PASS, acquire at least three additional independent Architecture sites and enough units to reach the 8-site/64-unit floor; freeze the independent JCI ontology/roster separately.
4. Run only the frozen smoke/audit path, then Architecture E1/E2/E3. Run JCI E2/E3 as an independent replication. Proceed to fresh E4 only if its prerequisites pass.
5. Write the paper around the one conditional-complementarity mechanism and its equal-information policy consequence. Negative or inconclusive gates must narrow the paper rather than be replaced by a different metric, subgroup, site exclusion, utility conversion, or baseline.

## Task 6 implementation closure and external-intake boundary (append-only, 2026-08-21)

- The synthetic-only pre-call design-lock validator is implemented and independently approved. Frozen repository SHA-256 values are `7d850554905062d7abc4bb81d899aebca1f0218cf1b3bc8bc11d65126f843b8b` for `iclr2027/precall_design_lock.py`, `8fea8d8149b2b257fa54d0e0532ccc6923c0e7444eac5f927efea570c7bb26f7` for `tests/test_iclr2027_precall_design_lock.py`, and `60a95e650cd3375ab824beff1f7c48141f81c938964b61c52ba6bb443e799d71` for the CLI. The final Task 6 report SHA-256 is `9591a4f2692c88c664ee32d78826972bf49f29462850d24cffe5d400892ebe84`.
- Final verification on those bytes passed focused `58/58`, adjacent `199/199`, and full discovery `714` passed with `9` platform skips and zero failures/errors; Ruff, compile, AST, CLI determinism, and pre-I/O `NEEDS_CONTEXT` boundaries passed. No model, controller, evaluator, baseline, source, result, held-out/OOD, simulation-draw, rate, tool, or paid-call access occurred.
- Independent final reviews are `task-6-implementation-review.md`, SHA-256 `418f32e9ecf3c717dc30c544d5c95aa43ae9c1cfc44a3e3f0a0dce70257286f8`, and `task-6-security-provenance-review.md`, SHA-256 `d31bd4106102a438047459948450935d39020dba7e1afbde5cd5a769f7f9cfbb`. Both verdicts are Critical/Important/Minor `0/0/0` within the synthetic-only scope.
- The validator cannot be upgraded by rehashing a result or gate: the result is exactly synthetic, `no_go`, unofficial, and bound to the deterministic current fact/lock/gate census. Gate predicates are recomputed rather than caller-trusted. Arbitrary comparison arrays have one JSON-native representation. The `1,024` terminal / `1,728` branch-call values remain shape arithmetic only; conditional compact eligibility is false because no execution-isolation/reuse authority exists. Multi-prefix increments remain `+16/+27`, and `9,216/13,824` remains unbound and forbidden.
- The upstream memory digest `e774381bbde93a9540821a6375ccbee55ec724d801e91b10efab2bcdc91083b6` is correctly upstream of Task 6 but its exact raw bytes are not recoverable from the current workspace. The current downstream memory must not replace it. Official source mode therefore remains `NEEDS_CONTEXT` until an external channel supplies the exact raw bytes plus a detached-signed immutable locator binding logical identity, positive raw length, raw SHA-256, UTF-8/no-BOM and LF/final-LF policy, immutable-store identity/version, capture provenance, key identity, and public-key digest. No local file may pretend to be that snapshot or receipt.
- The first safe local next artifact is only a non-authoritative acquisition checklist and synthetic negative fixtures for the external locator/anchor envelope. The first external blocker is the exact `e774...` raw snapshot plus signed locator and independently trusted non-CLI launcher capability.
- After that external blocker is resolved, freeze an actual Architecture hierarchy with at least 8 disjoint sites and 64 physical target units, split 3 sites/24 targets for audit and 5 sites/40 targets for focal evaluation. The historical 30 cases cannot substitute for typed targets. Freeze JCI project/ontology/target/prefix authority independently and never pool the two domains for inference.
- Next bind the approved Task 4B retained-handle source authority, the exact 22-policy method/model/version/readiness roster, token/cache/output ceilings, retry and failed-attempt billing rules, tool quantities and dated rates, scheduler/concurrency bounds, scientific deltas and noninferiority margins, power and precision targets, nuisance/dependence/missingness grids, seeds, and cost/time ceilings. Only an externally signed complete freeze may authorize zero-call simulations; only an authenticated design-lock PASS plus a separate one-use user approval may authorize any paid smoke or branch collection.

## External-authority acquisition lock (append-only, 2026-08-21)

- The non-authoritative acquisition contract is frozen at `task-7-external-authority-acquisition-brief.md`, SHA-256 `9323c725a7f7a0520fb6ad4f71657fae6808cc7fb6672f91c18f32e27f0b8a54`. Independent science and security/provenance reviews are respectively `task-7-external-authority-acquisition-science-review.md`, SHA-256 `a42811069e45a34ba1cb70ffc90f6e5253e53954042e263356efffa424e67146`, and `task-7-external-authority-acquisition-security-review.md`, SHA-256 `987c9e316e2c428fe2c0a6effc685ef0f46841ec72e6f462e3fae6194335b571`. Both final verdicts are Critical/Important/Minor `0/0/0`.
- This contract mints no authority. It defines two disjoint external paths. Path A recovers the exact legacy `e774...` raw bytes and authenticates them through a repo-external locator pin, immutable key/signature members, same-handle retrieval receipt, and independent review. Path B is recommended if those bytes remain unavailable: it explicitly declares no legacy continuity or equivalence, freezes a newly externally authored one-thesis contract from the three approved Task 5 authority pins only, signs a new upstream snapshot, obtains three distinct externally signed/pinned science/provenance/security reviews, and signs a migration receipt before any Task 6 vNext authority or implementation work.
- Path B must not derive from this current memory, any Task 6/Task 7 artifact, or the missing `e774...` prose. The exact legacy digest appears only as the searched-but-unavailable target inside the signed legacy-search declaration. The new one-thesis contract restates the frozen scientific roles under external scientist ownership: Architecture flagship; JCI separate unpooled E2/E3 replication; CATS baseline/motivation only; E1 predictive/noncausal/nonprimary; E2 randomized actually executed complete-bundle primary mechanism; E3 equal-information raw-router consequence with 22 readiness policies and a separate retrospective oracle; E4 fresh and downstream.
- The ontology-specific kill chain is symmetric. E2 failure in either Architecture or JCI kills the causal mechanism and ICLR-main OACS thesis. E3 null/parity-invalid after positive E2 in either ontology kills the OACS method and ICLR-main claim. No cross-ontology pooling or other-domain-only main-claim rescue is allowed; only the exact narrower descriptive/executed-bundle-effect report named by the acquisition contract may remain.
- The current executable state remains `NO-GO`/`NEEDS_CONTEXT`. No source, data, locator, root, key, signature, external approval, simulation, rate, model, tool, or paid call was created or consumed. The next nonlocal input is either the exact Path A legacy package or, preferably, an external owner/scientist decision to initiate Path B together with distinct signing/reviewer identities and key/package custody. Only after that chain is complete may Task 6 vNext be authored and re-reviewed; paid experiments remain later and separately authorized.

## Path-B negative-validator implementation closure (append-only, 2026-08-21)

- The user approved Path B as the preferred non-continuity workflow. That approval selects the acquisition route only; it is not an external scientist signature, reviewer signature, key, trust root, migration receipt, Task 6 vNext authority, design-lock PASS, simulation authorization, paid-call authorization, empirical result, or paper-acceptance evidence.
- The negative-only Path-B metadata validator is implemented under `task-7-negative-validator-implementation-plan.md`, SHA-256 `2616b8f11ba03725f5a2702f9548e069e9526aaee82236b21be973d0bdc706b5`. Frozen repository bytes are `a1bc28334f08d95ef551784b85c08007686c0de05f4f59499cf70cde429e20e5` for `iclr2027/external_authority_acquisition.py`, `66342f4f6cb97cab095963bf0c9c7aa86f55cb1ffbcf77edab2a156c9785048c` for `tests/test_iclr2027_external_authority_acquisition.py`, and `6e1e492431f1f249ff5c3c917e0790f2d46e75e26848cceabe38ca86971a2d1c` for its fixed-argument CLI. The final implementation report, including the superseding EOF chronology closure, is `task-7-report.md`, SHA-256 `e9c7cee115501519acc82c161ac96a25098e10f73689b3f6e23e0c3ee36a134e`.
- Final independent scientific/integration and quality/security/provenance verdicts are each Critical/Important/Minor `0/0/0`. The final focused suite passed `38/38`, adjacent Task 6 + Task 7 passed `96/96`, Ruff and no-write AST parsing passed, and all three CLI outputs were byte-deterministic. The final full discovery exited 0 after 203.6 seconds; a separate no-execution discovery counted 752 cases and 9 statically declared platform skips. No production/test/CLI byte changed after that run.
- The validator has exactly five public symbols and returns a deterministic synthetic `no_go`, unofficial result with 26 negative fixtures, 15 exact reason codes, and zero external artifact/signature/review/Task6-vNext counts. Authenticated acquisition raises exact `NEEDS_CONTEXT` before observing caller input. It performs no file/path/source/data/result/rate access, signature verification, key creation, network/process/model/tool/baseline/controller/evaluator call, simulation draw, held-out/OOD access, or paid work.
- Fully rehashed attacks now fail closed across exact Task5-only thesis literals, the byte-sorted 22-policy roster, symmetric Architecture/JCI kill and survivor rules, A10/EF423/current-task namespace exclusion, e774 declaration-only scope, terminal-NUL role domains, store/object/custodian evidence bijections, distinct external reviewer authority dimensions, and declaration-to-snapshot-to-three-reviews-to-receipt joins. Leaf/parser rejection and relational-root rejection are tested and reported separately; self-hashes remain integrity checks only and never authenticate external truth.
- The current scientific and operational state therefore remains `NO-GO`/`NEEDS_CONTEXT`. The exact next input is a real repo-external Path-B package: signed legacy-search impossibility declaration, externally authored one-thesis contract from the three Task5 pins only, signed new upstream snapshot, three distinct signed/pinned science/provenance/security reviews, and a signed migration receipt. Until those objects and their external custody exist, Task 6 vNext, zero-call simulation execution, data acquisition, paid experiments, and positive ICLR claims remain unauthorized.

## Obligation-hypergraph Phase-B theory decision -- supporting theory only (append-only, 2026-08-21)

- The approved theory design is `2026-08-21-obligation-hypergraph-theory-phase-b-design.md`, SHA-256 `fc3bd0ba946a62e8eabce4bab33d1c93797e4874e98dcb1bb9f417f017a8978e`; its execution plan is `2026-08-21-obligation-hypergraph-theory-phase-b.md`, SHA-256 `e64c72528eca596b037dac591f6f352074aa7e44c49175ee424d252c7c883073`. The final proof is `2026-08-21-obligation-hypergraph-theory-phase-b.md`, SHA-256 `d446e879ab68640f9a87e0edba7464581586b05ffcd9825198082be6e3c768b2`; the adversarial ledger is `2026-08-21-obligation-hypergraph-phase-b-counterexamples.md`, SHA-256 `640c4cd38e178efc6894115529b9eb857c74a762a2219865af26e39720db97f4`.
- The isolated primary-executor proof and novelty reviews are respectively `task-8-phase-b-proof-review.md`, SHA-256 `4b8a35fd61fb6283d7536bb3f18696e0f30cfb5b1fe9cdccc441843cbcb02758`, and `task-8-phase-b-novelty-review.md`, SHA-256 `8f37721b877b610211c9b7a2c91df8696f4c1d91bd274114690b2f3ac75f6d69`. Each reports Critical/Important/Minor `0/0/0` within the deliberately demoted scope. The mechanical gate is `task-8-phase-b-gate.md`, SHA-256 `fd0d9b1d4d657d8e4dc051fcbe36aa724c75633f8b03474d38005fa7e63951c6`.
- Frozen verdicts are: `B0=proved_observable_chronology`; `B1=proved_product_rate_conditional_bias`; `B2=proved_sparse_confidence_conditional`; `B3=valid_first_order_plugin_bound_only`; `B4=standard_sparse_lower_bound_only`; `B5=estimator_separation_only`; and `B6=insufficient_without_broader_search`. The final gate is `supporting_theory_only`.
- The strongest supported claim is an exact observable two-sample conditional product-bias identity for the frozen obligation-audit model, paired with a conditional sparse confidence radius and an honest first-order planned-action error decomposition. These results can support the empirical methods section and explain precisely where orthogonality helps structural estimation and where it fails to remove decision-time generated-feature error.
- The proposed theory headline is withdrawn. Phase B does not prove product-rate cumulative regret, a matching joint audit/execution minimax lower bound, or lower policy regret than an optimally tuned same-information plug-in/raw learner. The same-information lower bound proved here is only the standard `Omega(sqrt(T))` planned-action obstruction, and the coefficient-rate separation need not order the policy-relevant product `q theta`. The reviewed primary roster, especially BRACE, AMRIV, noncompliance bandits, sparse upper/lower theory, offline-oracle reductions, and fast best-in-class regret, also prevents a theory-first novelty claim from the surviving pieces.
- The paper direction remains the existing empirical E2/E3 thesis with this theory as support, not a replacement thesis. Current authenticated continuity remains 5 sites, 30 cases, 450 tasks, 1,524 prefixes, and standardized OACS branch coverage `0/6`; no empirical effect, power, feasibility, cost, acceptance, or positive-result claim follows. Source and Path-B external authority remain `NEEDS_CONTEXT`/`NO-GO` exactly as before.
- This Phase-B theory pass used no source artifact, data, result, held-out/OOD item, model, evaluator, controller, baseline, simulation draw, tool, rate, network execution, or paid call, and made no VCS mutation. The next scientifically valid move is to retain the supporting lemmas in the paper plan while waiting for the already specified repo-external Path-B authority chain before any Task 6 vNext, zero-call simulation execution, data collection, or paid experiment.
