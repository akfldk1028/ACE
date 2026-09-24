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

## OACS paper-blueprint integration gate (append-only, 2026-08-22)

- The claim-locked paper-integration design is `2026-08-22-iclr2027-oacs-paper-integration-design.md`, SHA-256 `b9bfad416a4e0631846ca83543cd17eeb99c1ee826eeaa6105f50cdb62749be6`. The inline execution plan is `2026-08-22-iclr2027-oacs-paper-integration.md`, SHA-256 `4aa425748611f8f8090e1a52e46d6bec2bec3b4fb59c858ef5ec4ddb95a46258`.
- The four English paper-control artifacts are frozen as follows: `claim_evidence_matrix.md` SHA-256 `1b09193a92e444827cce9470a91274fa1e4d3985a4ca13ee5c07bce772699294`; `paper_blueprint.md` SHA-256 `f489ef283ad5776209ebd5f49896af39083295b0cd988be9be0ed4ddc1e717b2`; `theory_appendix_map.md` SHA-256 `dc52a815afb2d84bd8021a3f3faaa173d0b3da31943f2bd29d4afd3e6c43595d`; and `reviewer_attack_matrix.md` SHA-256 `c286a2ffd02ff140a361e9a6063adc6385bbb29287d0d30da8e159f264fc8f53`.
- The isolated primary-executor claim review is `task-9-paper-claim-review.md`, SHA-256 `98094931cfe08b4dfd80d4353ac202e7367094475cc6f8051059a70e8dacb6e8`; the integration review is `task-9-paper-integration-review.md`, SHA-256 `924a97e8f414068d0f7d8398695a9d6aea49fe6feee4d71c96df4f075b982dc1`. Both report Critical/Important/Minor `0/0/0` within paper-architecture scope.
- The mechanical gate is `task-9-paper-gate.md`, SHA-256 `6a2355248c543152c372676f6189f82011a11a8f07818ff6f7b9030092b71449`. Its decision is `PaperBlueprintGateV1: paper_blueprint_ready`. This means the English manuscript can be drafted against a controlling claim registry; it does not mean empirical results, source authority, a complete manuscript, submission readiness, or acceptance readiness.
- The registry contains exactly 23 claims: 5 `READY` supporting-theory rows, 5 `STRUCTURAL_ONLY` design/role rows, 10 `BLOCKED` empirical/nonclaim rows, and 3 `KILLED` theory-headline rows. The exact 22-policy pre-outcome roster is frozen and the retrospective oracle remains separate and post-outcome only. Architecture remains flagship, JCI independent and unpooled, CATS baseline/motivation only, E1 predictive/noncausal/nonprimary, E2 primary, E3 equal-information consequence, and E4 fresh/downstream.
- The paper blueprint contains no empirical estimate or fabricated positive result. E1/E2/E3/E4, cost, safety, generalization, and acceptance language remains bound to exact future-evidence markers. Product-rate cumulative regret, joint audit/execution minimax optimality, and same-information policy superiority remain permanently killed. Supporting theory remains `supporting_theory_only`.
- The reviewer pre-mortem contains 24 unique attacks across 12 required families, including outcome-selected membership, planned/actual receipt mismatch, Architecture/JCI pooling, unequal information/compute, baseline readiness and version drift, retrospective-oracle leakage, denominator inflation, cost/retry omission, kill-chain rescue, score-to-regret promotion, and source-authority fabrication.
- This paper-blueprint phase performed zero protected source/data/result/held-out/OOD reads, model/evaluator/controller/baseline runs, simulations, rate lookups, network or paid calls, external-authority creation, Task 6 vNext work, or VCS mutation. The scientific execution state remains `NO-GO`/`NEEDS_CONTEXT`. The next safe local paper task is a separately controlled English LaTeX scaffold that preserves every claim ID and blocked marker; actual empirical completion still requires the real repo-external Path-B chain and later design-lock authorization.

## OACS LaTeX scaffold gate (append-only, 2026-08-22)

- The claim-locked English manuscript scaffold is under `AG-Research/docs/paper/iclr2027_oacs/latex`. It contains 15 UTF-8/LF files: `main.tex`, nine main-text sections, three appendices, `references.bib`, and `README.md`. The byte-ordinal ordered manifest SHA-256 is `4fc6ad9b497c54262fd3db16bba5e2055129f5926bc4426c0d7bdb1c6b3a7fcb`; `main.tex` SHA-256 is `929c1d24cbb9c2ee419031b25f9ca3f2fd7a6a985e1d71af1ba01cd077dab1ee`.
- The implementation report is `task-10-paper-latex-report.md`, SHA-256 `9e672cef138480be77762e714a8f5a25b1959140c2a490a07de0a63de23cabfc`. The isolated primary-executor review is `task-10-paper-latex-review.md`, SHA-256 `757bfd48f5fcc048919fadb96bdc4658258fa9c291263fc183704bf1beddb1c4`, and records Critical/Important/Minor `0/0/1`. The sole Minor is environmental: this host has no TeX engine, so rendered-PDF compilation is not claimed.
- The mechanical gate is `task-10-paper-latex-gate.md`, SHA-256 `aebc4e0d01c9b6b85b1c8b17fac516a27585226bcb52d099a58dbe1586b80abc`. Its exact decision is `PaperLatexGateV1: latex_scaffold_static_ready`. This is not a submission-ready, empirical-results-ready, PDF-verified, or acceptance-ready gate.
- Static integration verified 15 files, 12 `input` edges, balanced braces/environments, all 23 claim IDs with exact source-state equality, nine exact blocked result slots, the ordinal 22-policy roster, all 24 reviewer attack IDs across 12 families, the separate retrospective oracle, four resolved citations, and the supporting-theory/nonclaim boundaries. No empirical estimate was inserted.
- Architecture remains flagship; JCI remains a separate unpooled replication; CATS remains motivation/baseline only; E1 remains predictive/noncausal/nonprimary; E2 remains the randomized verified executed-bundle primary mechanism; E3 remains the equal-information policy consequence; and E4 remains fresh and downstream. The symmetric E2/E3 kill chain and exact narrower-survivor rules are unchanged.
- Product-rate cumulative regret, joint audit/execution minimax optimality, and same-information policy superiority remain withdrawn. Cost, safety, generalization, acceptance, and all E1--E4 numeric results remain blocked.
- No protected source/data/result/held-out/OOD item, model, evaluator, controller, baseline, simulation, tool, rate, network, paid call, Task 6 vNext authority, or VCS mutation was used. Scientific execution remains `NO-GO`/`NEEDS_CONTEXT`. A fresh TeX-enabled compile is the next local manuscript check; empirical work still requires the real repo-external Path-B authority chain and subsequent reviewed authorization.
## Task-11 literature correction and static-readiness closure (append-only, 2026-08-25)

- The binding specification is `D:\Data\25_ACE\AG\AG-Research\docs\superpowers\specs\2026-08-24-iclr2027-oacs-literature-build-design.md`, 27,798 bytes, SHA-256 `5924EBDBCA94814C538A4317967E4FA99DA96FFCC92F7E59F75B30D5D46798FD`; the binding plan is `D:\Data\25_ACE\AG\AG-Research\docs\superpowers\plans\2026-08-24-iclr2027-oacs-literature-build.md`, 22,342 bytes, SHA-256 `69ECC8B596FDAA7B0DBD01CFB796EA0753C4C325C119D96531677B5F403156F7`.
- The Task-1 report is `D:\Data\25_ACE\AG\.superpowers\sdd\2026-08-24-iclr2027-oacs-literature-build\task-1-report.md`, 16,727 bytes, SHA-256 `374AD0A22789954C2803A26BA85C4745DB60CB5BBC8EC6EA9C7ABD3224C8FA13`. The primary-source manifest is `D:\Data\25_ACE\AG\AG-Research\docs\paper\iclr2027_oacs\literature_primary_source_manifest.md`, 3,161 bytes, SHA-256 `9A84A93002562DFDE19008C759C960E809DB5CB11CB95CC7AE2790F4A98B7108`.
- The static verifier is `D:\Data\25_ACE\AG\AG-Research\iclr2027\paper_latex_verification.py`, 49,851 bytes, SHA-256 `9EC13684612E6FB34E58351359529DBBB897ECC6CD502B77E0A9D8CB0190C6A4`; its focused test is `D:\Data\25_ACE\AG\AG-Research\tests\test_iclr2027_paper_latex_verification.py`, 143,836 bytes, SHA-256 `7FF97D25BB5C4B0537CDA444843265E83747394533AF6B121DFAFAEEC68F19B4`; its fixed CLI is `D:\Data\25_ACE\AG\AG-Research\verify_iclr2027_paper_latex.py`, 1,385 bytes, SHA-256 `C43CEA36B8D12B93F51C58E003AA28D6D1CCAF3266AF44FA434E47DD9DEE3CA9`; and its read-only secure helper is `D:\Data\25_ACE\AG\AG-Research\iclr2027\secure_files.py`, 30,073 bytes, SHA-256 `2E9D0A710E249BB097316113A9BE1FB24A9FEA30295CB9CF88ADD164CDBB7FAB`.
- The final Task-2 report is `D:\Data\25_ACE\AG\.superpowers\sdd\2026-08-24-iclr2027-oacs-literature-build\task-2-report.md`, 57,783 bytes, SHA-256 `954BE26C741F095D764D8F82EC0B82140F6A586FDFB757A91A92E9FB9E4A6903`. The final literature review is `D:\Data\25_ACE\AG\.superpowers\sdd\2026-08-24-iclr2027-oacs-literature-build\task-11-literature-review.md`, 15,984 bytes, SHA-256 `78AEB9066BD0B37718E3C1FC9B35AE80FDD59D62EA6B713CD9258ED59447E547`; the final verifier review is `D:\Data\25_ACE\AG\.superpowers\sdd\2026-08-24-iclr2027-oacs-literature-build\task-11-verifier-review.md`, 8,813 bytes, SHA-256 `74A1E86D559862E1CC02737F5853AD1F9E1B680372741F4EE48729F057894F79`; and the final gate is `D:\Data\25_ACE\AG\.superpowers\sdd\2026-08-24-iclr2027-oacs-literature-build\task-11-paper-gate.md`, 6,188 bytes, SHA-256 `1E05CAAC054973BFBF923D8EBE74DCEADEEE77FB45FAB25670AA6B8E53BC16CD`.
- The final `PaperStaticReceipt` self-hash is `D2015B5C64D467DB36E741A75FEEDB4EFFC25D7896533CDF546C76591C76C8A4`; its canonical source-manifest SHA-256 over the 15-file manuscript closure is `41CC37C11B501C1C9D4778DD13052EB054B45134665AA7E6A8B4C010BFB695DB`. The final no-argument receipt stream was 845 LF-only bytes with SHA-256 `E2F7096CC36FFA4EA666A7867ED13BDF3C436C537A4DB5B29A75021677F4C7C5`.
- The Task-11 decision is `PaperLiteratureGateV1: literature_corrected_static_ready`. Fresh focused verification was 51 tests with 0 failures and 0 errors; the focused-plus-adjacent suite was 147 tests with 0 failures and 0 errors; Ruff, AST parsing, CLI help, and two byte-identical default CLI receipts passed. Full discovery ran exactly once: `python -B -m unittest discover -s tests -p "test*.py" -v` exited 0 with 803 tests, 9 skipped, 0 failures, and 0 errors; unittest reported 305.480 seconds and the enclosing command 312.556 seconds. One initial raw-byte capture infrastructure wrapper timed out after 60.038 seconds before it executed either default CLI check; its confirmed bare-Python orphan was terminated, an explicitly authorized replacement capture passed, and neither test nor discovery timed out.
- The literature/science review is approved with one nonblocking prose grammar Minor (finite-verb agreement in the ontology-wide nonestimability sentence); its test-quality verdict is C0/I0/M0. The verifier review is approved with correctness/security C0/I0/M0 and test quality C0/I0/M0. The Minor does not change the estimand, kill rule, or scientific interpretation.
- Preserve the one-thesis contract: Architecture is the flagship; JCI is an independent, unpooled replication; CATS is baseline/motivation only; E1 is predictive, noncausal, and nonprimary; E2 is the randomized verified executed-complete-bundle mechanism; E3 is the equal-information policy consequence; and E4 is fresh and downstream. The exact 22-policy pre-outcome roster remains distinct from the separate, post-outcome descriptive retrospective oracle. The symmetric E2/E3 kill chain, no pooling, and no cross-ontology rescue remain binding.
- PDF verification, compiler/archive/cache authentication, and rendered-document inspection are deferred to separately reviewed Task 12. Empirical state remains `NO-GO`/`NEEDS_CONTEXT`. This closure makes no empirical, source-authority, power, cost, safety, generalization, submission, or acceptance claim; it performs and asserts no protected-artifact/data/result access, model/evaluator/controller/baseline/simulation operation, paid call, TeX/PDF/compiler operation, network/rate research, or VCS operation.

## Unofficial OACS PDF preview closure (append-only, 2026-08-25)

- This block records a hardened disposable rendering check only. It does not amend, satisfy, or replace Task 12; it creates no authority receipt, official PDF gate, canonical artifact, reproducibility result, authenticity result, empirical result, venue-compliance result, submission-readiness result, or acceptance claim. The current static receipt deliberately remains `pdf_compile_verified=false` and `empirical_status=no_go_needs_context`; official scientific execution remains `NO-GO`/`NEEDS_CONTEXT`.
- The exact preview report is `D:\Data\25_ACE\AG\.superpowers\sdd\2026-08-25-iclr2027-oacs-pdf-preview\preview-report.md`, 8,672 bytes, SHA-256 `76A1E87D180C29CBFBDD2D7EEF0B12E7CAE15E782AAFB98F9E890FE870809F44`. Its independent narrow rereview verdict is Critical/Important/Minor `0/0/0` within the unofficial preview lane. The historical Task-11 gate above remains an immutable audit record for its old byte set and was not reissued or silently promoted for the current manuscript bytes.
- The successful `r4` output is an eight-page US-Letter PDF at `D:\Data\25_ACE\AG\.superpowers\sdd\2026-08-25-iclr2027-oacs-pdf-preview\artifacts\r4\main.pdf`, 101,983 bytes, SHA-256 `DBE003A2BB7AA0F1358FE0BFC38BD327B305DB2A1D79DD80703822AC73230EB9`. All eight original-resolution page renders and the contact sheet were reviewed. The independent review found no clipping, overlap, missing glyph, broken table/box, margin overflow, unresolved citation/reference, or TeX/font warning/error; one nonwarning lmtt font-information fallback had no visible defect.
- The current canonical 15-file OACS manuscript source-manifest SHA-256 is `FD6D73E7E87A9DDC710B6BDF0507A1143834CFD0019ADCEED4C59FCB4F1D29AC`; the independent active-prose aggregate is `F3C57C1E48E104D9B37DDF3A49202D5139FB279B779E2AF117D0368BE176A087`. The three source files changed in the render-fix loop are: `02_related_work.tex`, 3,358 bytes, SHA-256 `C3D0319A0154D691E6CA64F5307832C2E3B893FBA5F94CAF6F70C9D98CBBBD36`; `05_supporting_theory.tex`, 1,259 bytes, SHA-256 `735C6D809237FF9DCA2210EE6228F187AF367B838C06B9D276EFA0DE50F9C93B`; and `06_experimental_design.tex`, 1,592 bytes, SHA-256 `95A74A34EBA55E8B443280692CF1017C74C8AB86C843E79EFEF9A6AB6FC0E1C9`.
- The current verifier is 50,289 bytes, SHA-256 `A2C03F972A153511393CCE49AAFB6A303F5B5DD34F225ED6A7170F34E96E8448`; its focused test is 146,195 bytes, SHA-256 `BB04F86BD70E93DA5BC2578A8D175411A3C63BCCCCD3EA8F6998A28B70E63EED`; and the CLI remains 1,385 bytes, SHA-256 `C43CEA36B8D12B93F51C58E003AA28D6D1CCAF3266AF44FA434E47DD9DEE3CA9`. Fresh verification after the final edit was 54 focused tests and 150 focused-plus-adjacent tests, each with zero failures/errors; Ruff and AST parsing passed; two default CLI runs were byte-identical, LF-only, 845 bytes, with stream SHA-256 `9C3E1E1C0BDCEC408BBF566C99E86A7B0DAACA8842E322EBFD4B80EEBBCF545D9` and receipt self-hash `8EDB98CD306E601399832FE93F3881416E28E9DF74AC24B38DDE7C196DB48B9D`.
- The compile used Tectonic 0.17.0 as a pinned static musl ELF, a local read-only bundle directory of exactly 134,980 regular files, `--untrusted --only-cached`, fresh cache/output/tmp/profile roots, separate user/mount/PID/network/IPC/UTS namespaces, dropped UID/GID and capability sets, `no_new_privs`, and a post-drop seccomp boundary denying network, process creation, namespace/mount, ptrace, BPF, keyring, and related escape operations. No repository, home, credential, Docker, interop, or host `/proc` view was present in the child root. The upstream GitHub asset and bundle are unsigned; their byte hashes are preview-integrity observations, not publisher signatures, and WSL retains shared-kernel residual risk.
- The PDF visibly preserves the exact 22-policy pre-outcome roster, all 14 bibliography entries, nine blocked result slots, the retrospective-oracle separation, the E1--E4 roles, the theory withdrawals, the symmetric kill chain, and the source/empirical nonclaims. It contains no new estimate, powered result, policy superiority, source/version assignment, cost/safety/generalization result, or acceptance evidence.
- This closure performed no protected source/data/result/held-out/OOD research access, model/evaluator/controller/baseline/simulation run, paid call, empirical analysis, or VCS mutation. The next scientifically decisive dependency is still the real repo-external Path-B/source authority and reviewed empirical design-lock path. More cosmetic preview iteration cannot substitute for those inputs.

## Path-B external handoff closure (append-only, 2026-08-25)

- The bounded non-authoritative external work order is `D:\Data\25_ACE\AG\AG-Research\docs\paper\iclr2027_oacs\path_b_external_handoff.md`, 27,915 bytes, SHA-256 `6AC83C04D68AB30E1AB623A91AB1C53D6F212E57C3250468E01225156AD904D4`. Its independent focused test is `D:\Data\25_ACE\AG\AG-Research\tests\test_iclr2027_path_b_external_handoff.py`, 24,234 bytes, SHA-256 `FC0AFA1CC6012C410D489DCF5D1E6CCC18FA26F1E4F37F40E602D1B98381EB1A`.
- The implementation/audit report is `D:\Data\25_ACE\AG\.superpowers\sdd\2026-08-25-iclr2027-path-b-external-handoff\handoff-report.md`, 5,259 bytes, SHA-256 `1080EFA65A40610AEF706EA5A0F61B484F6E1BD205D106BD7269E0154F847724`. The final independent scientific/nonclaim, authority/security, and operational/test-quality reviews each returned Critical/Important/Minor `0/0/0` on the exact final handoff/test pins.
- Fresh final verification passed focused `10/10`, adjacent handoff plus existing external-authority suite `48/48`, and Ruff with zero failures/errors. The existing status interface remained deterministic synthetic `no_go`, `official_result_eligible=false`, with all external-artifact/review/signature, Task6-vNext, source/data/result/rate, simulation, model/tool, and paid-call counters zero. No full discovery was run for this documentation-only addition.
- The handoff is explicitly `INTAKE_ONLY`, `MINTS_NO_AUTHORITY`, `NOT_TASK6_VNEXT`, and `NO_SIMULATION_OR_PAID_AUTHORIZATION`. Its closed transport-only wrapper binds the exact Task-7 process bytes, exact legacy-search target, three Task-5 scientific parents, seven-role artifact/envelope/pin DAG, terminal-NUL domains, six-predecessor receipt without a self-cycle, 15 thesis scalars, ordered 22-policy roster, four endpoints, eleven kill/survivor clauses, exact reviewer record/envelope/pin dimensions, scoped approval fields, and three noninterchangeable custody/intake locator terms.
- The local Task-7 and Task-5 paths are sender-side transport candidates only. Before any external work, an accountable owner must independently re-home and reverify their exact bytes. Task 7 is process authority only and never a scientific parent; only the three externally re-homed Task-5 byte objects may become the new contract's scientific parents. Missing bytes, custody references, identities, signatures, reviews, pins, or immutable members require STOP.
- This closure creates no external scientist, custodian, migration owner, reviewer, key, signature, approval, trust root, immutable locator, Path-B package, Task6-vNext authority, design-lock PASS, simulation authorization, source/data permission, empirical result, submission-readiness claim, or acceptance evidence. The scientific state remains `NO-GO`/`NEEDS_CONTEXT`.
- The exact next nonlocal action is for a real external owner to produce the seven artifact records, seven detached-signature envelopes, seven separately approved external pins, all referenced immutable members, three independent `C0/I0/M0` migration reviews, and the final six-predecessor migration receipt chain under external custody. Only after a separately reviewed positive-intake design and external-rooted locator exist may this workspace evaluate that package and commission Task 6 vNext. Paid or empirical work remains later and separately authorized.

## OACS Statistical Analysis Protocol appendix closure (append-only, 2026-08-26)

- The binding design is `D:\Data\25_ACE\AG\AG-Research\docs\superpowers\specs\2026-08-26-iclr2027-oacs-analysis-protocol-appendix-design.md`, 20,300 bytes, SHA-256 `2083396AAC5DC1E10BB7EB9209330757A4293908AA027D49B61BF761765029AA`; the binding plan is `D:\Data\25_ACE\AG\AG-Research\docs\superpowers\plans\2026-08-26-iclr2027-oacs-analysis-protocol-appendix.md`, 10,235 bytes, SHA-256 `CA6004165C9235106FA10AFCF70B20038969AC9D721BADD707F3BE5D9DECB046`.
- The new frozen appendix is `D:\Data\25_ACE\AG\AG-Research\docs\paper\iclr2027_oacs\latex\appendices\appendix_analysis_protocol.tex`, 16,671 bytes, SHA-256 `FC09378D26E5B0BE504C57E4790F01A6E2B8892E84347EFDF5DAE7548E8FDDA7`. `main.tex` is now 2,377 bytes, SHA-256 `0FB07B0B1CC0F211A51C934683E1812E868316743744287D2F5150606B50EB51`, with exactly one new input between `appendix_theory` and `appendix_claims`. The current authenticated manuscript closure is 16 files; prior 15-file gates/previews above remain immutable historical records for their earlier byte sets.
- The final static verifier is `D:\Data\25_ACE\AG\AG-Research\iclr2027\paper_latex_verification.py`, 52,150 bytes, SHA-256 `7CCDCBFA0CA8A6082BF438E3DBD85A59F3BFF5AA4B7B1E20D6598A98A15570A1`; its independent focused test is `D:\Data\25_ACE\AG\AG-Research\tests\test_iclr2027_paper_latex_verification.py`, 176,492 bytes, SHA-256 `128EEF62D2F66D4A05F5AF0E7D80CEDF585365CB3CD58747F85EAA013ABBDFF1`. The fixed CLI remains byte-identical at 1,385 bytes and SHA-256 `C43CEA36B8D12B93F51C58E003AA28D6D1CCAF3266AF44FA434E47DD9DEE3CA9`.
- The final implementation/verification report is `D:\Data\25_ACE\AG\.superpowers\sdd\2026-08-26-iclr2027-oacs-analysis-protocol-appendix\task-1-report.md`, 14,560 bytes, SHA-256 `FE3DB85D9BF911A4C44E4974CAB1867034EBD5678D72CB10E72CBC6DDFC48B11`. The final scientific review is `task-1-science-review.md`, 5,846 bytes, SHA-256 `B69E95EAB42947E5A9B4AA43B2AED4B68D2C855BCF4F9F9FA8B56B7FB3661299`; the final verifier/security/test/report review is `task-1-verifier-review.md`, 5,852 bytes, SHA-256 `BE849B1ADD07D625057388A137822C1287B4BC09BC15979B26DA613AF161F523`. Both final verdicts are Critical/Important/Minor `0/0/0`.
- The final source-manifest SHA-256 is `816936B1F76A8CB87AC04720812FCBFEA284A0A435AC95E084EA9A1B0C23746B`; the active-prose manifest is `3C948537010223B4FEA869A41B8C3BBA64391524E3A1EE456A3A9BB9FDABBA53`; the production AST digest is `1039A7D8B1558B20ABE0FBB9CE7EF1E78F608AD8AE72C36180B7348DB178842F`. The deterministic receipt self-hash is `C657F604CCF7C3B9BDACA1B2ABDA1845EB5E70834A72952B18951B719815A2DA`; `source_file_count=16`, `pdf_compile_verified=false`, and `empirical_status=no_go_needs_context`. Two final CLI streams were byte-identical at 845 bytes, SHA-256 `074252EBA228A3DBD02F4BD166A174BFFE1D54B3F037B581495DA81F5A6B3DD7`.
- Strict TDD captured the initial four-test missing-appendix RED and three subsequent review-fix REDs before their implementation. Fresh final verification passed focused `61/61`, adjacent Path-B/external-authority/pre-call `106/106`, Ruff, AST parsing, and deterministic CLI. Full discovery ran exactly once after stable candidate bytes and exited 0: 823 tests, 9 skipped, 0 failures, 0 errors (`345.734s` unittest; `353.5s` enclosing wall time).
- The SAP freezes the E1 complete-menu predictive label, E2 same-site residual-present versus weighted residual-absent complete-bundle contrast, equal site/case/target/pair/repeat hierarchy, pre-outcome adequate-support/compliance criteria, sharp-null Fisher RI boundary, E3 direct-value regret and exact 15-field/seven-opportunity parity, byte-sorted 22-policy readiness family, separate descriptive oracle, Holm families, unpooled Architecture/JCI conjunction, pre-call STOP rules, diagnostic falsification gates, symmetric kill/survivor boundaries, blocked result shells, and exact nonclaims. It reports no observed value.
- The existing `path_b_external_handoff.md` is recognized by the verifier only as a metadata root sibling that is listed but never read. It remains outside source/active manifests, receipt count, scientific prose, and authority. This closure creates no Path-B authority, Task6-vNext PASS, authenticated source/data/result access, site/target sufficiency, power/MDE, cost/feasibility/runtime, simulation/paid authorization, positive E1/E2/E3/E4 effect, policy superiority, safety, deployment/generalization, official PDF/venue gate, submission readiness, acceptance probability, or theorem promotion. Scientific execution remains `NO-GO`/`NEEDS_CONTEXT`; the next decisive dependency remains the real repo-external Path-B package and later separately reviewed Task6-vNext authorization.

## ICLR 2027 official submission overlay closure (append-only, 2026-08-27)

- The binding overlay design is `docs/superpowers/specs/2026-08-27-iclr2027-official-submission-overlay-design.md`, 17,483 bytes, SHA-256 `C2A8D5744789C5607FA15A83C3AD61D665F38E0A199CC509E20114417FAA6205`; the binding plan is `docs/superpowers/plans/2026-08-27-iclr2027-official-submission-overlay.md`, 34,228 bytes, SHA-256 `F2B2B7340DE1D57E13FEE92825FBEA60E3FBE6A5A0F75EA70BD56DA04ED7533B`. The exhaustive Task 1--6 final report is `.superpowers/sdd/2026-08-27-iclr2027-official-submission-overlay/task-1-report.md`, 20,518 bytes, SHA-256 `5C9F89806A594BBD4A16573A03278407A18D4E6066920063145D5B009C5C23E6`; the completed progress ledger is 9,874 bytes, SHA-256 `317161A943573A983B9357221346F50FE3F77C3EAF9019AF9BC017C0F9A25D6C`.
- Official-format provenance is the frozen ICLR 2027 archive `https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip`, 39,348 bytes, SHA-256 `0D940DFA9398AE99A18F24A85A8A683F367204B6AF6D17D2899E60A67102529E`. The retained byte-identical runtime assets are `fancyhdr.sty` `B56EC4434B9F4607529A4B23DC68AD8D4B94F1F631C8CDDAF7DA78140D53A5EA`, `iclr2027_conference.bst` `2D67552DB7ED38CCFCCB5957B52F95656E25C249724761D3CF5F7922AD1844C5`, `iclr2027_conference.sty` `797DEEF41724E93761426AC0CBCCA46279A91CC650DD1F0CE76A4F08D2098EA6`, and `natbib.sty` `88BC70C0E48461934CAB5B2ACCEF06B74A8B3AC45AD03CCD3F2A6B7E0D6D530D`.
- Final governed code is `iclr2027/paper_latex_verification.py`, 72,962 bytes / `230BD500A227D8F4CC523564CFA1280FF6094D5D9AA5FC830017DCE7F680A381`; its focused test is 264,519 bytes / `90FAECD441BB9BC5CE46CA7B2C9D0CC959D8602B5033C4BC87F58152EAC91D87`; the CLI remains 1,385 bytes / `C43CEA36B8D12B93F51C58E003AA28D6D1CCAF3266AF44FA434E47DD9DEE3CA9`. Normalized AST identities are production 7,842 nodes / `3E2EE98E0F03DCA84E60E912C75FFCE60C477AE513F193732E01B72138033945`, tests 28,397 / `F9AF8A3FE9DAC764E3A21A68FFF40BCDB2D3139CACF2E61913B04A119BA72110`, and CLI 159 / `2645AD8276A116E25DBB8CB0DCC8F4557F03D2654996B8D7B7CD12E5F963B883`.
- The exact 21-file source manifest is `13add4f9cdbf3f871c58a3a5db88279bd8284cd7e925c5ad63232881f17b1a25`; the nine-source active-prose manifest is `b6a2a618f3e680eaa4e8949af1ac1e2b28e8af0fd96ae253067365f0de6848e9`; active main is `A27CD5B2110EA6DCE5CA258BE1614B1CEB8A6F2F99DB074887DA28092355912D`; active submission statements are `8ACA3C119BE02916E59BF5457A560CDD779693AB1ECABA168AA570D3176AB086`; the primary-source manifest is `9A84A93002562DFDE19008C759C960E809DB5CB11CB95CC7AE2790F4A98B7108`. Receipt self-hash is `9c182543d647523cdc476026ff766810784650d4d0889dfe66ee926f704b8643`, with `source_file_count=21`, `pdf_compile_verified=false`, and `empirical_status=no_go_needs_context`. Two raw CLI executions exited 0 with empty stderr and byte-identical 845-byte LF-only stdout, SHA-256 `16085133A7429950F9C14A603CD27A6211E8C7988CF70CC9E03C403336D2E780`.
- Fresh final verification passed focused paper verifier `90/90`, exact adjacent Path-B/external-authority/pre-call no-go `106/106`, Ruff, and `AST_OK 3`. Full discovery ran exactly once with `C:\Python313\python.exe -B -m unittest discover -s tests -p "test*.py" -v`: 852 tests in 396.450 seconds, 9 skipped, 0 failures, 0 errors; enclosing wall time was 405.384 seconds. No infrastructure failure occurred.
- The bounded unofficial round-5 preview is 12 US-Letter pages with counted main text ending on page 5, 15/15 embedded and ToUnicode fonts, no dangerous PDF features, and no warning/error/undefined/font-substitution/overfull/underfull-hbox findings; the two remaining page-fill vboxes on pages 3 and 11 were independently reviewed as benign. Its PDF is 100,092 bytes / `E6A00DC53FC2C9657B7BE23AA49DBE61E4DA389C4A0B49985DAAFD19497055A6`; preview report is 16,397 bytes / `0DC89A0B142789436D1EBE2F4F092514616BA697297BEF572C444DB58A0411F6`; independent final review is 14,556 bytes / `F1D2D9B1563C9DF4CA4452B0794006B728EDD1B2AF965A028DC54E3A69FB8560`, verdict `APPROVED__C0_I0_M0`. It is an unofficial format/layout preview only and does not change the receipt's PDF-false status; all-author factual/AI-use attestation remains pending.
- This closure removes the targeted official-format/static-verification blocker only. It claims no Path-B authority, design-lock PASS, authenticated data/results/models, power/MDE or feasibility decision, paid/simulation authorization, empirical effect or policy superiority, safety/generalization, official compile or venue clearance, submission readiness, acceptance likelihood, or theorem promotion. Scientific execution remains `NO-GO`/`NEEDS_CONTEXT`; real next blockers are the repo-external Path-B package and authority, a separately reviewed design lock, site/target and power/feasibility resolution, authorized execution, and later evidence/result review.

## Path-B Positive Intake Generation-0 closure (append-only, 2026-08-30)

- Final status is `GENERATION0_LOCAL_CLOSURE_VERIFIED__NO_GO_NEEDS_CONTEXT`. This is a local parser, relationship, public-verification, no-authority orchestration, and audit closure only. It creates no external launcher, trust root, locator, package, key, signature, approval, custody reference, authenticated success receipt, Task6-vNext authority, source/data/result permission, simulation or paid authorization, empirical result, submission-readiness result, publication-likelihood estimate, or acceptance evidence.
- The governing design is `docs/superpowers/specs/2026-08-27-iclr2027-path-b-positive-intake-design.md`, 21,032 bytes, SHA-256 `CF7FF5D2F105F1F1DA9C0A53937058672D65EB1ABDDD8C2B75F495C09D41597B`. The governing plan is `docs/superpowers/plans/2026-08-30-iclr2027-path-b-positive-intake.md`, 23,950 bytes, SHA-256 `2DEDA53D3774ED166901967C6C3BFB73131E049F9AEA287EA2DD610332EFCD42`. They are process specifications, not external authority or scientific parents.
- The science errata are closed on the reviewed manuscript bytes: the SAP uses exact `learner_class_capacity`; E2 is complete-bundle high-versus-low assignment within separately frozen residual-present and residual-absent strata, and residual status itself is not randomized. Final relevant pins are SAP 16,889 / `CE89C6169B2D91396E985E631C26B25BD9A221249927DD4879B1121FA674832C`, experimental design 1,876 / `20A759EE8E266D8CDB837139B1FE5AA04EEF5D5678AAD25E4952888527F8994F`, claim matrix 15,832 / `2048C5FDA7A0D2873B8FE59E953FF738AE0DE01C9271535C32013BDD4391E88B`, static verifier 72,962 / `17229EC5075F7E1F62676F882D5230922F3EFE1F41A495FAC4B27959284F3BCE`, verifier test 264,545 / `2FF5BCDD619D053C7E7AC72D5B995EA6841B32EF8EF7159845BAED59C801E579`, and science-alignment test 30,759 / `A0010AB0C6F8A51C279FA99281AC9395B5E8190D60CC162975430CC03F38299F`.
- The final unofficial reviewed preview is `main.pdf`, 100,577 bytes, SHA-256 `E613481718F2E9E6061F77DB6A7123413CE6BEFF1AB2442838424FE515E788CD`; its log is 15,330 / `545DAA3D9A403E17A750342D4F61D1D82A537DC6F04015892B6BCDA542D571DC`, artifact manifest 5,153 / `070C48980929ED034E4652B9AAC2B1903AD1E22CB7612B3A76599C82ADCD7B15`, and report 5,800 / `E2ADF7CBD1B7174109BF8B03FB0B618971202722DC6A688CDB39D8ADDAC0F9D2`. It is 13 US-Letter pages with counted main text ending on page 5 and was independently inspected. Repository truth deliberately remains `pdf_compile_verified=false` and `empirical_status=no_go_needs_context`; the preview is not an official compile, venue clearance, or submission gate.
- Final Generation-0 production pins are: canonical contract 29,663 / `79F736548AD9DD05D08921CD5E474E611432EBFA748D61DA53ABEE84E8F0C26F`; science/relationships 42,990 / `29127CEAE4D2AA15EC6080C76DAA32ABD0F0E7FD25F969BA83DCEB12B89FECD2`; public-only Ed25519 verifier 4,876 / `22536551EED74C20F30E2BDCD5F0A911AF839F60A35C2FCB47F08E433C50864C`; no-authority orchestrator 8,007 / `1FE99C846DA781E71CD029C0455B0C30CBAE116E704CB4951C63B352AA2E05F2`; and deterministic CLI 2,041 / `3BC483D27C1CDADFFDD347243A8E00E6982A1C685ADD954CDD0D056D9D6CEAB8`.
- Final Generation-0 test pins are: contract 69,169 / `EFEF828533428DA4BFA6767AD2A82E2A35DDC83138712ACF56BF64FBC1B9C767`; science 118,927 / `57B0B5059BB9B770F2DEE1E59AF44A6C8510F7E7717B5FE4D1B34564782CD617`; crypto 25,297 / `CE74A8A5E606F44F87878B944F0ADE60A372A03D9249A54A1E4D80CC78E18BA7`; orchestrator/CLI 37,046 / `2B87F193F22FA5BADB6C7984F5688EF8C831142BAF93D6582641D12229D85161`; and refreshed model-neutral handoff test 10,606 / `CC1D25011989BC6FFAFA23887757A4B3A03E470948FB96C96F7961F451309E6A`.
- The completed adversarial integration report is `.superpowers/sdd/2026-08-30-iclr2027-path-b-positive-intake/task-7-worker-report.md`, 38,124 bytes / `83CDFC4D577DC6C49336C83D16E10E65074350B285BDDF01632D6F3E245BBF5A`. Its final science review is 42,197 / `412D602DD87D6F96627A92E1EEDE7FCEFF2DFE55F8B6CF765497DCF146A770DD`, verdict `APPROVE__C0_I0_M0`; its final security/code-quality review is 48,154 / `7AA6F418A22985370D5C0BFD0E7F13C272398B14BEA98CBC6297541B84EC075E`, verdict `APPROVED__C0_I0_M0`. The final contract closes the complete typed `66 + 3*C + E` physical inventory and the science layer closes the canonical `272 + 9*C + 2*E` global occurrence census for nonempty variable custodian count `C` and evidence count `E`, while required relational mirrors are counted once.
- Final verification passed handoff `5/5`, science-alignment plus paper `118/118`, positive-intake `130/130`, adjacent no-go `196/196`, explicit AST/source policy `14/14`, and Ruff lint. Full discovery was invoked exactly once as `C:\Python313\python.exe -B -m unittest discover -s tests -p "test*.py" -v` and passed 1,015 tests with 9 skips, 0 failures, and 0 errors in 427.199 seconds (433.8 seconds wall). It covered the frozen implementation and pre-Task8 documentation-expectation bytes. The authorized final handoff expectation/document delta was then verified separately by the focused `5/5` contract; discovery was not rerun.
- Raw deterministic evidence remained stable: paper CLI 845 bytes / `7D0B6B3CE492EF05820AC2E1033FE576B9AD9FD305BBCCBD6A490DAA8F6A98AC`; positive-intake status 1,026 / `CFACA4263773F64CCFD3D171FD08CEA0189FCAB59621D5CA5FFEED619A009EBF`; negative-fixture registry 3,198 / `FEE94E1D51093366137EEC90561506077823493C26976FEEB5E5877801BC31B0`; help 323 / `1B0FFE2CFBCACF5BD72DEF74EB5AA4BB6670A60A830DAD87238CF9BBB19DF228`; fixed invalid-argument stderr 25 / `7A1B569D0999A0F1049733371C7D759F6C4840C31EC88C1D1A53D424A7FE2301`.
- The final model-neutral handoff is `ICLR_2027_OACS_HANDOFF.md`, 10,430 bytes / `9AF826ADAD89505A8A2B68A1559AA781B3E2D83CCF291E2A23F59EBBAF341FA0`. `CLAUDE.md` is 388 / `073E8703D7167AAEFE79F7B725B91518B90FC3413FAF3F61F795208CA0EAD848` and directs Claude, Codex, and other agents to the handoff plus this append-only memory. The Task-8 final report is `.superpowers/sdd/2026-08-30-iclr2027-path-b-positive-intake/task-1-report.md`, 18,873 / `E17B0E0C345C090F7E73E11EDD9FCD2F780581B10E3270C3C4B34AA948194278`. Its independent handoff/science-status review is 11,978 / `00E8DF8B1EBEEA538FB8A16DE8ACACF34DF5F8D788B9ACA60670C4DD361206AE`, verdict `APPROVE__C0_I0_M0`; its replacement exact-file verification review is 7,677 / `7872A16376332E12C1C30DE20BFC6EB0BC958569CEF282E956EC4D788A4F7D08`, verdict `APPROVE__C0_I0_M0`.
- One initial Task-8 verification-review run was invalidated and excluded after its reviewer reported an unintended broad stale-scan read of fragments under `results/**`. It performed no write, network, VCS, or execution action. The replacement reviewer used an exact allowlist of files, performed no directory enumeration or protected/results read, and supplied the approved review pin above.
- Deterministic current state is: `authority_mode=external_bootstrap_absent`, `status=no_go`, `empirical_status=no_go_needs_context`, `synthetic_only=true`; `task6_vnext_commission_eligible`, `source_access_authorized`, `simulation_authorized`, `paid_run_authorized`, and `official_result_eligible` are all false; all 24 authority, I/O, operation, retry, fallback, and downstream counters are zero. The empirical planning interface still reports only 5 Architecture sites, 30 historical cases, and standardized action coverage 0/6; authenticated Architecture/JCI site/typed-target rosters and the conditional 8-site/64-target planning floor remain unresolved.
- Exact next sequence for any future agent is: (1) accountable external owners independently re-home and verify the Task-7 process bytes and three Task-5 scientific-parent bytes; (2) create the external trust policy, native launcher/platform pin, root keys, locator policy, rotation/revocation head, and one-use challenge outside the repository; (3) create the immutable complete 21-record Path-B package, all referenced members, four custody objects, approvals, signatures, and three independent migration reviews; (4) approve a separate Generation-1 amendment and run authenticated positive intake; (5) only after that commission and independently review Task6-vNext authority; (6) run the reviewed design lock, resolve site/target rosters and power/feasibility, and freeze a zero-call simulation plan; (7) obtain separate one-use simulation and later paid/data authorization; (8) execute and independently review evidence/results before changing any empirical or manuscript claim.
- This append preserved the prior memory state as the required exact 79,410-byte prefix: pre-append SHA-256 `35A9F60FAC7824ECB6EAE3EF12255BEC1866D581C93D5C87770229A2E45C00F7`, first-4,096-byte SHA-256 `6A654314987C873060B0B137DE47B0C529F8BA1816AFE30BE6AA33AC70707C6A`, first line `# ICLR 2027 Architecture-Domain Memory`. No file mutation is permitted after this append in the current closure turn; only read-only prefix, heading-count, encoding, and full-hash checks follow.

## Task-9 validator hardening and next literature gate (append-only, 2026-08-31)

- Task 9 is `COMPLETE__C0_I0_M0_WITHIN_GENERATION0_SCOPE`. Its plan is `.superpowers/sdd/2026-08-30-iclr2027-path-b-positive-intake/task-9-validator-hardening-plan.md`, 6,659 bytes / `32DA8EE9D67896CB2A6C56FF684FDFFCFF41F72ABC2215EFF8880FD7B81936EE`; its final worker report is 10,778 / `795ABF4E9121DD5452D62C753B91BD71D0907B2579CBD5514021C2580FD7F6B7`.
- Final production pins are contract 31,625 / `65AD68287083623F013A634AC496DE876F7FF4F3F871EB7940EDF063E99AB3D8` and science 44,266 / `1F7998CB90857FBDF744505BC18B4DDCD5EC8018908BCC7592522042B5D762B4`. Final test pins are contract 81,598 / `8131AF52F581FB56B5B22D2FBCC4B43D52DCD15AB20CF627D8BB720BD566052C`, science 129,172 / `0D32F0E500B0B68D4CD3BB3D7352C0063E84365B7642904D5A073367437AF7FA`, and model-neutral handoff 12,623 / `40A091B8B8C5C5373C9873887C50EDD795009E41FBED4A3FB91246861F75DF04`. Current handoff bytes are 10,453 / `44564B80BCEE692B3417CED3ED147C916CB5DB84810BDB72E64AFABE10282EFC`.
- The contract now rejects caller-minted/reordered core roles, noncanonical/impossible approval timestamps, and Windows-illegal member characters. Its public structural self-hash parser owns exact canonical UTF-8/LF bytes, expected schema and self-hash field, recomputed self hash, and immutable file metadata without claiming semantic or external authority. The science validator applies that structural binding to each of the exact 7 artifacts, 7 envelopes, and 7 pins. This does not invent a legacy-evidence semantic parser and does not authenticate private core semantics.
- The final tests independently mutate all 21 core coordinates through both public validators, detect deletion of each of the three loop binding calls, accept literal UTF-8 while rejecting an equivalent escaped serialization, reject an independently resealed unsorted object, and detect drift in all four canonical-JSON keyword settings. The handoff test recomputes size/SHA-256 for all 25 file-backed rows; the in-memory source manifest and deterministic receipt remain correctly classified as nonfile objects.
- Independent code/test rereview is `.superpowers/sdd/2026-08-30-iclr2027-path-b-positive-intake/task-9-validator-hardening-code-review.md`, 11,732 / `99088E555ABEFE67A1B1D21E01CBF8C98BF3BBCDC1A6E2E16CB79CBAF7F9DE66`, verdict `APPROVED__C0_I0_M0`. Independent handoff rereview is `task-9-validator-hardening-handoff-review.md`, 8,692 / `5AA1C38C985982C9B03B432C41831676F6266AC21DB00671540F96659ED919A5`, verdict `APPROVED__C0_I0_M0`. The latter independently matched 25/25 file pins, accepted the pseudo-object exclusion, and closed the initial review-status overclaim.
- Fresh evidence on the final reviewed code/test/handoff candidate includes contract+science 99/99, final combined Positive Intake plus handoff 148/148, adjacent authority/design-lock/external-handoff/LaTeX 196/196, Ruff lint/format clean, and two deterministic `python -E -B ... --current-status` streams at 1,026 bytes / `CFACA4263773F64CCFD3D171FD08CEA0189FCAB59621D5CA5FFEED619A009EBF`. Full discovery was not rerun; the prior exact-once 1,015-test discovery remains historical evidence for its earlier frozen bytes, and the Task-9 delta is covered by the focused and adjacent runs recorded here.
- The state remains `authority_mode=external_bootstrap_absent`, `status=no_go`, `empirical_status=no_go_needs_context`, and `synthetic_only=true`; all source/simulation/paid/official authority flags remain false. This closure claims no authenticated Path-B, source/data/result access, empirical readiness or result, official PDF/venue gate, submission readiness, publication likelihood, or acceptance evidence.
- The next paper-acceptance work item is the frozen read-only literature audit `.superpowers/sdd/2026-08-30-iclr2027-path-b-positive-intake/task-10-references-literature-review.md`, 11,150 bytes / `04CCF3014B743978D7C4A23C3C00D6A0471894C65C72A59BA2441923E1652525`, verdict `C2/I3/M1`. Critical 1 is the absence of a public source/citation map for the headline 22-policy E3 roster; public papers should be cited now while adapter/version authentication remains separately blocked. Critical 2 is weak peer-reviewed novelty positioning relative to controlled coordination and exact roster methods.
- Task 10 must first use primary publisher/proceedings records to distinguish OACS from controlled matched-resource collaboration, graph/topology optimization, pruning, routing, debate, and multi-agent frameworks. Prioritized anchors are Kim et al. (Nature Machine Intelligence 2026), GPTSwarm (ICML 2024), AgentPrune (ICLR 2025), MasRouter (ACL 2025), More Agents Is All You Need (TMLR 2024), multiagent debate (ICML 2024), AutoGen (COLM 2024), AutoMix (NeurIPS 2024), and RouteLLM (ICLR 2025). The narrow novelty is a preregistered residual-obligation by receipt-verified complete-bundle mechanism test and equal-information comparison, not the first graph, router, selector, orthogonal score, or regret algorithm.
- Task 10 must also remove the unsupported generic off-policy-evaluation framing unless a real logged-policy component is specified; separate DML score orthogonality from the manuscript's own first-order decision-error proposition; move or explicitly delimit tangential regret/theory citations; and normalize BibTeX types, DOI/eprint/version fields, volume, and protected acronyms. Any manuscript/reference edit must begin with independent citation/source tests, update the authenticated source/active manifests and verifier pins under TDD, preserve all empirical nonclaims, and receive fresh literature plus static-verifier review before a new unofficial preview.
- This append preserved the prior memory as an exact 88,338-byte prefix with SHA-256 `EA433ABC03E9CC8FD00410D79582D77B06E26061970AAFF935EA886C4DEC028C`. No file mutation is permitted after this append in the current closure turn; only read-only prefix, unique-heading, UTF-8/LF, and full-hash checks follow.

## OACS policy-provenance and layout-fix static closure (append-only, 2026-08-31)

- Final status is `POLICY_PROVENANCE_STATIC_CLOSURE_VERIFIED__DISCOVERY_DOCUMENTATION_RED_CLOSED_FOCUSED__NO_GO_NEEDS_CONTEXT`. This is an ICLR 2027 conference-paper literature, provenance, static-verification, and unofficial-layout closure. It is not a journal workflow, empirical gate, implementation-authentication result, official compile, venue clearance, submission-readiness result, publication-likelihood estimate, or acceptance evidence.
- The governing design is `docs/superpowers/specs/2026-08-31-iclr2027-oacs-policy-provenance-related-work-design.md`, 16,912 bytes / `1C314F7D882C4685CBB47CF9DB6D805A6976A472F0EAD85492361EEB9F932F65`; the governing plan is `docs/superpowers/plans/2026-08-31-iclr2027-oacs-policy-provenance-related-work.md`, 42,793 / `C66F744F70A261CE20C5A50634ABCA2FF3A0B4BD48AE24B23A34FBAB27C62987`; and the non-authoritative 21-record public-source census is `.superpowers/sdd/2026-08-31-iclr2027-oacs-policy-provenance/public-source-census.md`, 9,942 / `78C561414136757DF32803C51F1AD3D4F937D43448472486048C9C3AAEFB4F73`.
- The exact ordered 22-policy appendix is `docs/paper/iclr2027_oacs/latex/appendices/appendix_policy_provenance.tex`, 11,825 / `FB369CE6755337A8C893E2857D0175A152445C21E11CFCF69C22478DB9FAAFFB`. Public bibliographic provenance is complete for the registry's published method families, while every adapter/version/configuration/parity/executable identity remains `blocked_pending_authenticated_roster`. Protocol-defined comparators remain explicitly protocol-defined, and the retrospective oracle remains separate and post-outcome.
- Final governed verification pins are production 92,048 / `51DAFF058AC1A95AD2581E3E9AA6EFC8B48D7F19661012101621BA0652A6BAD3`, focused test 354,903 / `09DBCC5F6C895DACC34475571740B71538BADA8BC11A9E1F61F3EFA0E820275F`, science-alignment test 39,256 / `2435F9D88346345D416773BD7B7B2EDFA6937A09F0C812BF5F0BF6F7122F7BA1`, and CLI 1,385 / `C43CEA36B8D12B93F51C58E003AA28D6D1CCAF3266AF44FA434E47DD9DEE3CA9`. The 22-source manifest is 2,275 / `EBFB0EC6F85C66AFBFB21AC4AEA87D760D3CAFF3F8546EAFFD767B235D9D1B91`; the ten-active-prose manifest is `F691CBDB102D65068780349B91FD4F4EA2E857746D1844C8AAF3F3C4DF290DA6`.
- The deterministic static receipt remains `schema_version=ace.iclr2027.paper_latex_static.v1`, `citation_authority_status=blocked_pending_authenticated_roster`, `pdf_compile_verified=false`, and `empirical_status=no_go_needs_context`. Its canonical JSON is 844 bytes / `1B612275AC7BBAE17FF317E3C5E7F1A486C042FBF7FB5BB803B752E2D1200600`; the CLI LF stream is 845 / `5A9F2B776C808C4EAD185762012719C5B523A4E1DB4C2C483CA7E86990808A48`; receipt self-hash is `d78ecc37c45cd249608434b97befd252b711992573dc9b8f527a20e1b79d606d`.
- The final worker report is `.superpowers/sdd/2026-08-31-iclr2027-oacs-policy-provenance/task-1-worker-report.md`, 24,690 / `167A3E642F50C9F96C02AB57067E3B16FA316A8B210484E27A4C4BDF47C8E878`. The literature review is 19,575 / `B37B383CB48817480DF6F27E46DCF9256C0A26CA443D8DE87A66F32540781C5E`, verdict `APPROVED__C0_I0_M0`; the verifier review is 12,363 / `0CBA4C2F206F383A69F79FA00EA70493AEF955F9D73EAD694C2A33667E15ED7F`, verdict `APPROVED C0/I0/M0`. Those reviews cover the pre-layout scientific tokens. The later layout-only raw bytes have exact active-token reconstruction, mutation closure, static, compile, and visual verification, but local checks do not mint a new independent authority.
- The layout fix added only local `small` and `raggedright` scopes around the policy registry. Its TDD RED was two methods with three missing-scope failures; subsequent layout/underfull, parser/mutation/scanner/AST, 102-method focused, and 136-method science/adjacent no-go gates were GREEN. Ruff check and format-check were clean, and two static CLI streams were byte-identical with empty stderr.
- A fresh offline one-shot compile ran exactly once in the distinct frozen root `.superpowers/sdd/2026-08-31-iclr2027-oacs-policy-provenance/preview-artifacts-layoutfix-01`; controller and compile return codes are zero and no retry occurred. The final 16-page US-Letter PDF is `output/main.pdf`, 118,088 / `2D1452A18278F238A3E24C40A9DB5716D3DF7EE5262961358017E38EC26FD639`. Counted main text ends on page 7 and the appendix begins on page 8. The final log has zero underfull/overfull hbox/vbox, undefined-reference, font-substitution, warning, or error findings. All fonts are embedded with ToUnicode, dangerous PDF features are absent, and all 16 full-resolution page renders plus the contact sheet were visually approved with no clipping, overlap, glyph loss, margin escape, broken table, unintended blank page, or anonymity leak.
- The successful preview tree is frozen at 52 regular files, five directories, zero links/specials. Its 51-row `artifact-manifest.tsv` is 4,873 / `FEAD1F5E382CDF713819A0534C3C253E47ABF270861F54992FBEDF5BA26926D9`, and every row was independently rehashed after freeze. The external preview report is 8,243 / `70F1E72902B5D02384A56D6A21163FA2220F970F40C0102774026336820B8649`, status `STATIC_PREVIEW_APPROVED__EMPIRICAL_NO_GO`. The consumed one-shot compile must never be rerun; a future compile requires a new root, nonce, and reviewed one-shot cycle.
- Full discovery was invoked exactly once after PDF approval and reported 1,042 tests in 490.817 seconds: 1,040 passes, nine skips, and two failures. Both failures were documentation-only stale-pin checks in `CrossAgentHandoffTests`, caused by the required pre-refresh handoff still naming the prior verifier, focused-test, and alignment-test bytes. No production, manuscript, policy-registry, scientific-boundary, PDF, transaction, or execution test failed. Discovery was not rerun. The authorized handoff expectation/document delta then followed TDD and passed its dedicated 7/7 suite plus Ruff; final handoff is 12,271 / `F05373106C2F6D2D4C7BA829357968C0EF40B646EED44DF478CE169792DDB7F6`, and final handoff test is 14,595 / `91EB5F858181E3BAAADD260C1181BAC79D9F684B6557FFBA402A656C64E413C0`.
- Acceptance-oriented assessment: the static manuscript now has a coherent ICLR thesis, explicit peer-reviewed positioning, an exact 22-policy provenance registry, a seven-page main paper, disciplined claim withdrawals, and a clean 16-page preview. These remove literature, provenance, and layout blockers but cannot support an acceptance probability. The decisive remaining evidence is empirical: compliant positive E2 effects must survive independently in Architecture and JCI, then E3 must establish the equal-information policy consequence without information/compute asymmetry; implementation provenance, power/feasibility, cost, safety, and external-validity claims remain separately gated.
- Exact next external sequence remains: (1) accountable owners provision the complete repo-external Phase-2 bootstrap; (2) review and freeze a Generation-1 amendment against those exact external bytes; (3) run authenticated Generation-1 intake through the externally pinned launcher; (4) commission and independently review Task6-vNext authority; (5) run the separately reviewed design lock; (6) resolve site/target rosters and power/feasibility; (7) obtain separate simulation and paid-execution authorization; (8) execute and independently review evidence/results before changing any empirical, submission, or acceptance claim.
- This append preserved the prior memory as an exact 94,332-byte prefix with full SHA-256 `AB957BD1FA6718B4816B9BED6A8F3F76CD05A989ED73D54A2D4142C3C93E9313`, first-4,096-byte SHA-256 `6A654314987C873060B0B137DE47B0C529F8BA1816AFE30BE6AA33AC70707C6A`, and first line `# ICLR 2027 Architecture-Domain Memory`. No file mutation is permitted after this append in the current closure turn; only read-only prefix, unique-heading, UTF-8/LF, final-LF, file-pin, artifact-manifest, and full-hash checks follow.

## Estimand-specific receipt study direction (append-only, 2026-09-01)

- The user approved a new acceptance-oriented research direction after the
  completed evaluation-validity manuscript was judged technically
  submission-ready but scientifically high-risk because it contains no fresh
  prospective result. This append does not alter that historical manuscript,
  its final PDF, or its immutable V1 diagnostic.
- The target remains the ICLR 2027 conference. The primary domain remains
  Architecture, but the new experiment is explicitly a public synthetic typed
  Architecture receipt benchmark, not a real 8-site/64-target roster and not
  an architectural-design performance result.
- The governing design is
  `docs/superpowers/specs/2026-09-01-iclr2027-estimand-receipt-study-design.md`.
  The working title is `When Is Planned Coordination Evaluable?
  Estimand-Specific Receipts for Multi-Agent Experiments`.
- The new paper question is which randomized-assignment, verified
  complete-bundle, and policy-value estimands remain identifiable under
  assignment, execution, target-binding, terminal-state, scorer-key, and
  version failures. The blanket all-receipt-failure rule is replaced by an
  estimand-survival lattice.
- The mathematical scope is component-specific observational equivalence,
  bounded contrast error for target/key misbinding, terminal
  misclassification attenuation and sign reversal, and a no-selective-rescue
  corollary. Receipts remain necessary observability conditions rather than
  proof of semantic truth or causal value.
- The planned zero-paid-API study uses a deterministic scripted five-domain
  Architecture workflow, an independent construction ledger, fully resealed
  upstream faults, completion/hash/trace/receipt-ablation baselines, and a
  preregistered Monte Carlo analysis of false estimability, bias, coverage,
  type-I error, false-sign probability, nonestimability, and overhead.
- No external paid API, protected source, held-out/OOD namespace, `data/`,
  `results/`, `models/`, historical V1 rescore, model/provider execution,
  simulation result, or empirical manuscript claim is authorized by this
  memory append. The current empirical state remains `NO-GO`/`NEEDS_CONTEXT`
  until the new design receives its first formal review, an implementation
  plan is approved, and simulation execution is separately authorized.
- Exactly two formal independent scientific review rounds are budgeted: one
  combined mathematics/experiment/novelty review before implementation and one
  integrated ICLR-style review after frozen results and the final manuscript.
  Automated tests, deterministic reruns, proof checks, and PDF inspection do
  not create additional review rounds.
- AI assistance is used as separated research roles rather than an endless
  prose loop, and all use in mathematical claims, proofs, experimental design,
  implementation, interpretation, and writing must be disclosed under the
  ICLR 2027 author policy. Human authors remain responsible for every claim,
  citation, proof, result, and artifact.
- The immediate next step is user review of the written design, followed by a
  detailed implementation plan. No code or manuscript edit precedes that
  approval boundary, and no VCS mutation is authorized.

## Estimand receipt formal-review closure (append-only, 2026-09-01)

- The user approved the initial study direction. Formal scientific review
  round 1 of exactly 2 is now complete; the three isolated mathematics,
  experiment, and novelty/ICLR roles all returned `REVISE`.
- The union meta-decision rejected vote-based consensus and preserved every
  Critical and Important finding. The original design remains the immutable
  review input at 20,850 UTF-8/LF bytes with SHA-256
  `E2A5D760C47DFDB7F4FC6CDB0AFB2D068323FD71F38AD745656A644AFD6851A3`.
- The corrected v2 separates canonical potential outcomes `Y*` from measured
  `tilde Y`; defines natural-execution ITT, controlled complete-bundle effect,
  and natural deployment-policy value; and replaces blanket
  `nonestimable` language with `CERTIFIED`, `BOUNDED`, and `NOT_CERTIFIED`
  relative to the registered observation and measurement model.
- The generic observational-equivalence theorem is no longer claimed as new.
  It is an agent-experiment binding specialization with exact finite-support
  paired worlds and explicit nonrecoverability conditions. The error bound is
  overlap-aware, terminal misclassification includes arm-specific sign
  reversal, and selective rescue distinguishes full-sample, MAR-recoverable,
  and MNAR-nonidentified cases.
- The benchmark now requires an immutable external trust root, a 3,584-object
  public fully resealed census, an independently authored one-shot 24-case
  held-out pack, 11 fair evaluators, and a secondary offline transport check
  over Apache-2.0 AgentTelemetry tag `v0.1.0-aiware2026`. AgentTelemetry does
  not become Architecture or causal-effect evidence.
- The registered simulation contains 255 primary and 42 ICC-sensitivity
  scenarios, 2,000 replications each, exact Philox namespaces, site-level
  `t_7` inference, explicit eligible-retention and false-reportability metrics,
  numeric GO/NO-GO thresholds, and an 8 CPU-hour/16 GiB/5 GiB ceiling.
- The corrected specification is
  `docs/superpowers/specs/2026-09-01-iclr2027-estimand-receipt-study-design-v2.md`;
  formal review evidence is
  `.superpowers/sdd/2026-09-01-iclr2027-estimand-receipt-study/task-1-review.md`;
  and the implementation plan is
  `docs/superpowers/plans/2026-09-01-iclr2027-estimand-receipt-study.md`.
- The current scientific state remains `NO-GO`/`NEEDS_CONTEXT`: no code,
  public-source acquisition, simulation, new result, V1 rescore, manuscript
  empirical edit, paid/model/provider call, protected-path access, or VCS
  mutation occurred during formal review 1.
- Formal scientific review round 2 remains reserved for the frozen result,
  final manuscript, and PDF. Automated TDD, theorem checking, mutation census,
  determinism verification, lint, and PDF inspection do not count as extra
  formal review rounds.

## Estimand receipt external-source correction (append-only, 2026-09-02)

- Task 1 of the corrected implementation plan is complete and task-reviewed.
- The earlier statement binding the 170-row Inspect dataset to AgentTelemetry
  tag `v0.1.0-aiware2026` is superseded. The tag exists at commit
  `1e9bf995bb97709e0ddecbd1f4100ed5a183e189` but its tree does not contain
  `src/agenttelemetry_inspect/data/traces_v1.jsonl`.
- The external transport fixture is instead pinned to the same repository's
  immutable first dataset commit
  `8ba0ae753d51cc2837f4ef2fa450e103c3be904a`. It must be described as a
  commit-pinned post-release public dataset, not as the tag snapshot and not as
  Architecture or causal-effect validation.
- Frozen source identity: 612,561 bytes, 170 strict UTF-8/LF rows, SHA-256
  `99a3e63f5a7a2eb25f5c1fd9ea62f80181f44e2d5a0d1096877c18f4cbd7cb49`,
  parsed canonical-row SHA-256
  `ea6c3f74202dae212da5c51e684f49e1bbe206311013e8b97fa2ce9700ec08ef`.
- Frozen Apache-2.0 license identity: 11,239 bytes, SHA-256
  `87e71eab2d4ec25ebe384daf6436a9c8afb54a26bc7f22bcc0642075d64bda10`.
- Exact admissible intake is
  `.superpowers/sdd/2026-09-01-iclr2027-estimand-receipt-study/external-source-intake-v3`.
  Empty v1 and v2 roots remain as fail-closed evidence of the wrong tag path
  and the superseded raw-whitespace parser contract.
- No downloaded upstream code was imported or executed; no paid/model/provider
  call, protected-path access, V1 rescore, experiment, or VCS mutation occurred.

## Estimand-receipt registered result and final acceptance status (append-only, 2026-09-02)

- The target is the ICLR 2027 conference, not a journal. The surviving paper is
  an ML evaluation/causal-measurement methods paper. `Architecture` is only an
  8-site x 8-target synthetic stress vocabulary; the paper is not a real
  building-performance or architectural-engineering study and must never be
  described as one.
- Tasks 1--11 of the estimand-receipt study are complete. Exactly two authorized
  registered 2,000-replication executions over 297 scenarios were retained.
  Their five scientific payloads are byte-identical. No third registered run,
  simulation retry, result rescore, paid API, live model/provider call, or
  protected-data experiment is authorized or scientifically needed.
- Frozen full-gate descriptive totals are 0/1,408,516 fatal false reports,
  373,484/373,484 compatible retention, 354,574/373,484 certified-cell
  coverage, and 4,479/89,660 null rejection. The old pooled
  Clopper--Pearson intervals are superseded: shared replicate data across
  estimands and heterogeneous scenarios invalidate an exact iid-binomial
  interpretation. Only point totals and scenario-row heterogeneity summaries
  remain manuscript claims.
- A read-only post-hoc extraction of the already frozen 9,801 metric rows
  recovered the missing structural comparison. For the target-relevant
  one-family faults E, B, T, S, G, and P, the full gate made zero unsupported
  reports and the corresponding one-component ablation reported every
  unsupported case. This is meaningful implementation/structural stress
  evidence against a co-designed oracle, not independent empirical
  validation. The pre-specified held-out/external macro comparison was not
  preserved and must not be reconstructed or claimed. Its post-hoc wrong-
  population proxy margin is only 3.359 percentage points, not the 10-point
  criterion.
- The manuscript is now in the official ICLR 2027 style with seven pages of
  main text plus references/mathematical appendix, ten primary references,
  explicit finite-roster estimands, three reviewable propositions/proofs,
  exact V2/V3 and post-hoc-custody disclosures, and no internal Task 7/Task 11
  language. Current six-source manifest is 556 bytes, SHA-256
  `438DD63831097F8938412C69D3589A557E6952FD135A53FD74FBB63437B8ADE3`.
- The sole Task 14 official-style PDF compiled successfully but failed the
  authors' stricter raw-release gate on one 0.66643-pt table overfull hbox and
  one badness-10000 underfull result line. All nine pages were inspected
  diagnostically and have no clipping, overlap, missing glyph, broken equation,
  or anonymity leak. The exact PDF is readable but internally non-final and
  must not be submitted without a separately authorized layout-clean build.
- Formal scientific review round 2 of exactly 2 is closed. After Task 14, the
  nine original findings are 5 ADDRESSED / 4 PARTIALLY_ADDRESSED / 0
  NOT_ADDRESSED; active severity is 0 Critical / 2 Important / 2 Minor. The
  final disposition is WEAK REJECT, score 4/10, with a broad planning band of
  10--25% acceptance conditional on a raw-clean PDF. It is venue-format
  submission-eligible but not acceptance-competitive. Final review identity:
  41,755 bytes, SHA-256
  `76D150E5E60D608C5E6726E110F9B5491075B76E6DA5A5168D5453947305F78E`.

### Anti-loop rule and the only acceptance-changing next task

- Do not start another manuscript-only pivot, another generic AI review,
  another 2,000-replication simulation, another pooled-interval calculation,
  another literature-only loop, or another PDF compile before new independent
  scientific evidence is frozen. Those actions cannot address the two active
  Important acceptance risks and caused the prior repetition.
- The only material next task is one clean, independently authored,
  outcome-bearing blind challenge of the receipt semantics. It must be authored
  without access to gate/oracle implementation details, include explicit
  potential-outcome laws and hidden correct support states for all three
  estimands, contain balanced valid/invariance/harmful cases across
  `Z,A,E,B,T,S,G,P`, and evaluate all 11 configurations under the same reveal
  boundary.
- Before any reveal, freeze and externally timestamp the pack, public
  projection, evaluator/analysis bytes, configuration order, exact filters,
  and decision thresholds. Minimum scientific thresholds are full-gate macro
  balanced accuracy at least 0.95, at least 0.10 above the strongest non-full
  comparator on the same blind population, zero harmful false reports, and
  zero valid/invariance false nonreports. `BOUNDED` remains a third state, not a
  synonym for either binary outcome.
- Execute that blind gate exactly once. Any pack/harness failure before a
  semantic verdict may be disclosed and versioned, but a post-reveal repair
  cannot be called pristine confirmation. If the clean blind comparison is
  absent or fails, stop trying to raise ICLR acceptance through wording and
  choose a scoped synthetic-methods venue or collect genuinely external
  outcome-bearing evidence. If it passes, add only that result, perform one
  layout-clean official ICLR build, and request a bounded disposition of the
  existing round-2 Important findings rather than a third formal review.
- A public AgentTelemetry schema-transport check alone does not satisfy this
  task. A real-trace extension must use independently supplied outcome/fault
  labels and compare the full gate with the same baselines; it must remain a
  trace-support result, not a real-building causal claim. No paid API is
  required for the minimum blind challenge.

## MAS headline restoration and final topic hierarchy (append-only, 2026-09-02)

This section supersedes the prior choice to treat the estimand-receipt paper as
the surviving headline paper and supersedes the statement that an independent
receipt-semantics blind challenge is the only acceptance-changing next task.
Those entries remain above solely as an audit trail of the completed pivot.

- The single headline topic is **Multi-Agent Systems (MAS)**. The paper asks
  whether coordination that is verified as actually executed improves
  decision quality over a single agent, and under which coordination and
  failure conditions that improvement is trustworthy.
- `Architecture` is one structured engineering **test domain inside the MAS
  study**, not the headline topic and not a claim that the paper is primarily
  an architectural-engineering contribution. Its role is to supply difficult,
  auditable constraints and heterogeneous specialist responsibilities.
- The preferred Architecture task is evidence-grounded compliance review over
  sourceable obligations such as site identity, use, gross floor area, floor
  count, building coverage ratio, floor area ratio, height, parking, and other
  legally supportable fields. Interior-layout or generative-design claims must
  not be added without rights-cleared geometry and objective ground truth.
- Execution receipts, estimand binding, terminal-state correction, mutation
  closure, and the completed synthetic study are **supporting measurement and
  reproducibility infrastructure**. They are not the paper's headline result
  and do not by themselves establish that MAS coordination is beneficial.
- The unifying research question is: **When actual execution is verified, does
  multi-agent coordination outperform a single agent on structured engineering
  reasoning, and what execution failures erase or reverse that benefit?**
- The required primary comparison uses the same frozen Architecture cases,
  evidence, model/backend, token and tool budget, and adjudication rule across
  a single-agent control and predeclared MAS coordination treatments. Candidate
  treatments may include routing, shared memory, reflection, debate, or other
  already implemented structures, but the final treatment census must be
  fixed once before outcome execution rather than expanded post hoc.
- Primary outcome families are engineering decision error (especially false
  approval and missed violations), evidence-grounded correctness, and verified
  treatment completion. Cost and latency are secondary efficiency outcomes.
  Receipt correctness is a validity condition or mechanism variable, not a
  substitute for task performance.
- The current receipt-focused ICLR manuscript is therefore a reusable methods
  component and historical artifact, not the final scientific story. The new
  MAS paper must not claim positive coordination value until a real
  single-agent-versus-MAS execution supplies that evidence.
- This is not a restart from zero. Reuse the existing MAS implementations,
  Architecture obligation schema and cases where provenance permits, receipt
  and verifier stack, estimand/statistical machinery, mutation tests, primary
  references, and official ICLR style. Rebuild only the scientific center:
  title/abstract/claims, the controlled MAS comparison, Results, and the
  conclusion justified by that comparison.
- Anti-loop rule: do not run more estimand-receipt simulations, generic AI
  reviews, receipt-only blind packs, manuscript-only pivots, or repeated PDF
  builds before the MAS experiment design and evidence boundary are frozen.
  Do not represent prose improvement as acceptance improvement.
- Acceptance cannot be guaranteed. The present receipt-only manuscript remains
  weak-reject evidence. Material acceptance improvement requires an honest,
  adequately controlled outcome-bearing MAS comparison; an unfavorable result
  must be reported rather than repaired through framing.
- The next controlled deliverable is one reviewed MAS experiment specification,
  followed by one implementation plan. No new experiment execution, provider
  call, paid API use, or manuscript rewrite is authorized merely by this memory
  correction; execution receives its own explicit approval after the design is
  frozen.

## User-approved MAS/OACS direction and acceptance harness (append-only, 2026-09-02)

- The user explicitly approved restoring MAS as the dominant paper topic and
  emphasized that its importance must remain visible throughout the project.
  The selected scientific direction is the existing OACS causal-mechanism
  thesis, not a new generic MAS-versus-solo ranking exercise.
- Final problem statement: current coordination policies use difficulty,
  confidence, topology, or generic transcript state, but these do not identify
  which residual obligation can be closed by which actually executed
  specialist capability. The paper tests the claim: **Hard is not enough;
  collaboration pays when residual work matches a real capability advantage.**
- The hierarchy is binding: `MAS headline -> residual obligation--capability
  alignment mechanism -> OACS policy -> execution receipt as measurement
  support -> Architecture as one domain test -> JCI as separate unpooled
  replication`. Architecture is never promoted above MAS and receipt is never
  promoted back into the headline.
- Strategic direction review ranked the candidates `OACS > topology-aware
  termination > estimand receipt` when each receives its decisive missing
  experiment. The termination direction contains existing runs but cannot
  currently support its central quality-preservation claim because of failed
  runs, missing online quality outcomes, a dimensionally weak utility proxy,
  and low human-scoring reliability. The receipt paper remains technically the
  most complete current artifact but scientifically weak-reject and too
  incremental for the headline.
- Public review-harness audit found no authoritative acceptance-producing
  prompt. ICLR 2027's four questions, PaperBench's separation of candidate
  production/fresh reproduction/rubric grading, MARG's specialized roles, and
  AI Scientist's structured review mechanics are useful. AI Scientist-style
  same-pipeline self-review, opposed accept/reject priors, few-shot anchoring,
  reflection as proof, and ensemble score averaging are not acceptance
  evidence.
- The project therefore uses two formal scientific reviews only. Before
  outcomes: isolated problem/novelty, causal/statistical,
  experiment/reproducibility, and adversarial-falsifier roles, followed by a
  meta-review that preserves every Critical and Important finding. After frozen
  outcomes: independent claim/evidence, mathematics/statistics, fresh
  reproduction/provenance, adversarial, and concise ICLR decision reviews,
  again with no score averaging and exactly one final internal verdict.
- The approved restoration design is
  `docs/superpowers/specs/2026-09-02-iclr2027-mas-oacs-restoration-design.md`,
  14,089 UTF-8/LF bytes, SHA-256
  `D8B90898741B33ABF65BC9A7412DA093C8C7466474636D71290F898BB81F7E0F`.
  It contains no placeholder, has a final LF, and passed the inline consistency
  review.
- This approval authorizes the design document and its later implementation
  plan, not a model/provider call, paid API, outcome execution, held-out reveal,
  result claim, manuscript rewrite, PDF build, submission, or VCS mutation.
  The next gate is user review of the written design, then a detailed plan that
  begins with inventory, admissible-domain census, parity, backend/cost, power,
  and pre-outcome claim-ledger checks.

## MAS/OACS pre-outcome plan approval checkpoint (append-only, 2026-09-02)

- The user approved the written MAS/OACS restoration design and instructed the
  project to proceed carefully with all review prompts aligned to the accepted
  harness.
- The first implementation plan deliberately stops before outcomes. It builds
  canonical contracts for the claim ledger, isolated review roles, Architecture
  and JCI admission censuses, same-information/same-budget treatment parity,
  zero-generation backend audit, prospective cluster power, and one conjunctive
  preflight receipt.
- The plan's review prompts implement the official ICLR four questions, exact
  claim/evidence citations, strongest accept and reject cases, explicit
  falsifiers, and isolated problem/novelty, causal/statistical,
  experiment/reproducibility, and adversarial roles. Initial reviews are
  hash-locked before a union-preserving meta-review. Score averaging and
  same-pipeline self-approval are prohibited.
- The plan is
  `docs/superpowers/plans/2026-09-02-iclr2027-mas-oacs-preoutcome.md`,
  35,120 UTF-8/LF bytes, SHA-256
  `DFCE7FCCA15E1CAB51F0D39ACFC0ABBD372E6DE0B30D51D2073E5A7890C660A5`.
  It contains nine independently testable tasks and passed spec-coverage,
  placeholder, path, command, and interface-consistency checks.
- The only terminal statuses of this first plan are
  `NO_GO_NEEDS_CONTEXT` and `GO_FOR_SEPARATE_EXECUTION_PLAN`. Even the latter
  does not authorize an experiment. Actual E2/E3/E4 execution requires a
  second plan and a new explicit user approval.
- No code, experiment, provider/API call, protected-data access, held-out
  reveal, manuscript/PDF action, submission, or VCS mutation occurred while
  writing this plan.
