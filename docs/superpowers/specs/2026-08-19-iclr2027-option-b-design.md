# ICLR 2027 Option B Preregistration and Method-Lock Design

Status: approved prospective amendment  
Effective date: 2026-08-19 (Asia/Seoul)  
Scope: development trajectory snapshot, CATS training/calibration, replay, held-out/OOD evaluation, site-aware statistics, and submission gating

## 1. Status and interpretation

This document records Option B after development trajectory collection had started but before CATS training, calibration, method lock, or held-out/test access. It must be described as a prospective amendment, not as a pre-data preregistration. The interrupted `pilot_full_v10` is operational incident evidence only. A provenance-clean replacement run supplies the development snapshot.

Option B is selected over:

- a monolithic analysis script with late threshold selection, rejected because it cannot physically enforce leakage and test-access boundaries;
- an online adaptive policy during trajectory collection, rejected because it changes messages and invalidates prefix-only counterfactual replay;
- Option B's modular contracts, selected because every claim can be bound to immutable inputs, explicit access gates, and reproducible receipts.

## 2. Lifecycle

The only permitted stage order is:

1. preregistration receipt;
2. complete development transaction snapshot;
3. physically separated prefix features and private labels;
4. grouped train/calibration assignment;
5. CATS training and trajectory-level conformal calibration;
6. development replay and development success gate;
7. method lock receipt;
8. held-out and OOD experiment matrix execution;
9. site-aware statistics;
10. table, figure, claim, and submission gate generation.

A failed gate does not permit threshold changes on later data. It either returns the workflow to an earlier development-only stage with a new amendment receipt or reduces the scientific claim.

## 3. Frozen study contract

Primary values:

- future-benefit threshold: `epsilon = 0.02` on normalized quality;
- conformal risk level: `alpha = 0.10`;
- consecutive no-benefit patience: `patience = 2`;
- primary classifier: histogram gradient boosting;
- model sensitivity: logistic regression;
- epsilon sensitivity: `{0.01, 0.05}`;
- alpha sensitivity: `{0.05, 0.20}`;
- development group assignment seed: `20260819`;
- CATS development median token reduction gate: at least `15%`;
- development mean quality difference `Delta Q` 95% confidence-interval lower bound: greater than `-0.03`;
- primary held-out median token reduction gate: at least `20%`;
- recommended CATS observed unsafe stops on frozen architecture test: `0`;
- held-out-model quality-margin violations: `0`.

The contract freezes feature schema, label definition, group keys, split assignments, classifier family, calibration rule, hard guard, baseline registry, metrics, multiplicity correction, and claim downgrade rules before held-out access.

## 4. Split and sample-unit contract

The indivisible assignment group is the site/case-family group. It contains both native and challenged conditions and every topology/repeat derived from that case family. Therefore no site, native/challenged pair, topology instance, or repeat from one family may cross train, calibration, development-gate, or test boundaries.

Development groups are assigned deterministically to train, calibration, and development gate using the frozen seed and a stable hash rank, with assignment performed before feature fitting. Assignment must preserve whole groups and report the resulting stage, decision, program, condition, and topology census. If exact target proportions conflict with group integrity, group integrity wins and realized proportions are reported.

Held-out architecture sites, held-out topologies, and held-out models remain outside all train/calibration/development-gate assignments. The 450 development runs are repeated measurements, not 450 independent samples.

## 5. Data and privacy boundaries

Each logical development run is one immutable transaction. The clean snapshot must contain exactly 450 planned identities and bind:

- frozen run plan and manifest;
- public case packet hash;
- prompt hash;
- actual code and runtime-dependency identity;
- raw message sequence and per-message hash;
- parsed prefix states and deterministic quality breakdown;
- agent, selector, control, and retry usage events;
- retry lineage and final status;
- all derived ledger row counts and hashes.

Runtime features and private supervision are separate physical artifacts with different schemas and paths. Runtime feature rows may contain only information observable at prefix `t`. They must not contain or derive from:

- gold records or gold issue codes;
- future turns or future quality;
- private condition labels;
- mutation family or mutation identity;
- final trajectory token count;
- final outcome, final stop turn, or hindsight oracle values.

Private label rows may contain `quality_t`, `future_max_quality`, and `beneficial_future`, keyed only by an opaque row identity. Tests must perturb all future turns and private fields and prove the runtime feature vector is byte-identical.

## 6. CATS definition

For trajectory `j` and prefix turn `t`:

`y_jt = 1[max_{k>t}(Q_jk) - Q_jt > epsilon]`.

The classifier estimates whether beneficial future improvement remains using prefix-only scalar features. Text fitting occurs on train groups only; calibration and test text never fit vocabulary, normalization, imputation, or model parameters.

Trajectory-level conformal calibration uses one nonconformity maximum per calibration trajectory so sequential repeated testing is controlled at the trajectory level. The finite-sample corrected `(1-alpha)` quantile is serialized with calibration trajectory IDs, source hashes, feature order, library version, epsilon, alpha, and model parameters.

Runtime stopping is:

`STOP_t = calibrated_no_future_gain_t AND admissible_t AND patience_2`.

The architecture hard guard has final authority. Malformed/incomplete state, missing required evidence, an inadmissible decision, or a guard failure forces `CONTINUE`. CATS can only truncate a natural trajectory; it cannot generate, rewrite, route, or repair messages.

## 7. Replay contract

Replay never calls an LLM and never creates messages. It applies every policy to the same immutable natural trajectory and returns a prefix ending at an existing turn. Prefix message hashes and cumulative usage must equal the source transaction through the selected stop turn.

The common policy registry contains exactly:

1. full natural termination;
2. max-message cap;
3. keyword termination;
4. legacy lexical-delta policy;
5. semantic-stability patience;
6. logistic predictor;
7. uncalibrated gradient-boosting predictor;
8. state-wise conformal ablation;
9. trajectory-calibrated CATS;
10. CATS without the architecture hard guard;
11. hindsight oracle peak stop.

Only the oracle may read future quality. Every other policy receives the identical runtime-prefix interface. Development online/offline parity uses 20 preselected development trajectories and is an implementation check, not a new performance table.

## 8. Usage and cost contract

Usage accounting is event based. It records agent inference, selector inference, deterministic control, retry attempts, failed attempts, and successful attempts separately. Each event binds run identity, turn/control index, provider/model, input tokens, output tokens, cached tokens when available, duration, and cost or an explicit `unavailable` reason.

Visible agent-message tokens alone are not invoice-grade accounting. If selector, control, or retry usage is absent, reporting must block monetary savings, total-compute savings, and invoice-grade cost-reduction claims. Token-only claims must name the included boundary.

## 9. Held-out and OOD access control

Held-out artifacts must not be opened, enumerated into feature code, summarized, or passed to analysis before a positive method-lock receipt. Test-access code requires the receipt hash and verifies that the following are frozen:

- study contract;
- development snapshot receipt;
- feature schema and fitted transforms;
- train/calibration/development-gate assignments;
- trained CATS artifact and calibration quantile;
- baseline registry;
- replay implementation hash;
- usage schema;
- statistics and reporting specifications.

The experiment matrix enumerates every planned held-out site, condition, program, topology, repeat, model, policy, and OOD axis before execution. Missing, duplicated, retried, or extra keys are reported; no failed row is deleted.

## 10. Statistical contract

Primary comparisons are paired within the same natural trajectory. Resampling and uncertainty operate at the site/case-family level:

- outer bootstrap resamples sites;
- case families are resampled or retained as paired clusters within sampled sites;
- all conditions, topologies, repeats, and policies for a selected family remain together;
- means, medians, IQRs, quality differences, unsafe-stop rates, premature-stop rates, overshoot, oracle regret, and usage reductions are reported;
- heavy-tailed token outcomes use median/IQR as the primary descriptive summary;
- CATS comparisons against multiple non-oracle baselines use Holm correction;
- site, topology, task, and model OOD coverage is reported separately;
- 450 trajectory rows are never analyzed as 450 independent observations.

## 11. Reporting and claim gates

Tables, figures, and claims are generated from receipt-bound analysis outputs. The main report includes policy quality/usage, unsafe and premature stops, calibration coverage, held-out/OOD coverage, retry/parse failures, and the controlled three-agent subset.

The submission gate blocks the strong “risk-controlled savings” claim unless every frozen primary criterion passes. A negative gate remains visible and automatically downgrades the claim to calibration/diagnostic evidence. It never hides results or triggers post-test changes to epsilon, alpha, patience, margins, feature schema, or quality weights.

## 12. Module boundaries

- `study_contract.py`: immutable epsilon, alpha, patience, split, success, and access contracts.
- `artifact_receipts.py`: canonical serialization, SHA-256 binding, row census, and tamper verification.
- `trajectory_ingest.py`: strict 450-transaction snapshot validation and materialization.
- `trajectory_features.py`: prefix-only runtime feature production and separate private supervision production.
- `cats.py`: classifier fitting, trajectory-level conformal calibration, serialization, and architecture hard guard.
- `policy_replay.py`: common interface and exact 11-policy registry over existing prefixes.
- `usage_ledger.py`: agent, selector, control, and retry accounting with claim availability flags.
- `experiment_matrix.py`: exact held-out/OOD plan, completeness checks, and method-lock enforcement.
- `statistics.py`: site-aware paired bootstrap, clustered summaries, and Holm correction.
- `reporting.py`: receipt-bound tables, figures, claim matrix, and submission gate.

Each module has one public responsibility, typed inputs/outputs, canonical schemas, and failing tamper/leakage/access tests before implementation.

## 13. Non-negotiable invariants

- No site/case-family group crosses a split.
- Test data is unreadable before method lock.
- Runtime features contain no gold, future, private condition/mutation, or final-token information.
- Replay only truncates existing trajectories at an existing prefix.
- Missing selector/control/retry usage blocks cost-savings claims.
- Statistical inference treats site/case-family clusters as the sampling units.
- Raw transactions are append-only; derived ledgers are reproducible and disposable.
- Any provenance mismatch fails closed and creates a new run namespace rather than impersonating an older code identity.
