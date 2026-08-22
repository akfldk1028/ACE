# ICLR 2027 CATS + Architecture Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` to execute this plan task by task, and `superpowers:verification-before-completion` before any completion claim.
>
> **Agentic workers:** do not spawn workers unless the user explicitly selects subagent-driven execution; if selected, isolate independent tasks and review each result before integration.

**Goal:** Preserve the existing multi-agent termination study, add a tested `STOP/CONTINUE` method with trajectory-level risk calibration, and validate it on a frozen full-architecture evidence benchmark in time for ICLR 2027.

**Architecture:** ARR remains the only geometry/legal/program source of truth. A new `iclr2027` package converts ARR artifacts into immutable public/gold case pairs, runs the existing 13 multi-agent systems plus the solo baseline with architecture-specific roles, deterministically scores every turn, trains CATS without future-score leakage, and replays termination policies on the same trajectories. Each run is committed as an atomic, immutable transaction; derived JSONL/CSV ledgers are rebuilt atomically from those transactions. Split manifests are frozen before test runs.

**Tech stack:** Python 3.11+, AutoGen-based existing AG runner, ARR Django management commands, standard-library dataclasses/JSON, pandas, NumPy, SciPy, scikit-learn, matplotlib/seaborn, `unittest`, LaTeX.

**Scientific spec:** [ICLR_2027_ACCEPTANCE_DESIGN.md](./ICLR_2027_ACCEPTANCE_DESIGN.md)

**Global constraints:**

- Never overwrite Exp01–Exp07 raw results.
- Never expose gold labels or mutation manifests in agent prompts or runtime feature rows.
- Never tune method, threshold, `ε`, `α`, quality weights, or prompts on the frozen five-PNU test set.
- Preserve ARR execution identity, geometry hash, program hash, and evidence provenance.
- All policies except the online parity check use the same recorded full trajectory.
- Do not add multi-action routing, RL, aesthetics, UI work, or a third cross-model provider before submission.
- Stop before primary runs if the pilot gate fails.

---

## Task 1: Freeze the factual audit and repair legacy claim inconsistencies

**Files:**

- Create: `AG/AG-Research/tests/test_iclr2027_audit.py`
- Create: `AG/AG-Research/iclr2027/__init__.py`
- Create: `AG/AG-Research/iclr2027/audit.py`
- Modify: `AG/AG-Research/config.py`
- Modify: `AG/AG-Research/validate_results.py`
- Modify: `AG/AG-Research/latex/main.tex`
- Modify: `AG/AG-Research/paper_draft.md`
- Modify: `AG/AG-Research/paper_draft_kr.md`

### Step 1: Write the failing invariant tests

Test the exact current facts:

```python
class ResearchAuditTests(unittest.TestCase):
    def test_system_count_is_thirteen_multi_agent_plus_solo(self):
        self.assertEqual(len(PATTERNS_ALL), 14)
        self.assertEqual(PATTERNS_ALL.count("solo"), 1)

    def test_exp05_is_not_described_as_trained_estimator(self):
        text = MAIN_TEX.read_text(encoding="utf-8")
        self.assertNotIn("quality estimator trained on exp02", text)

    def test_validation_uses_complete_exp01_summary(self):
        self.assertEqual(resolve_exp01_summary().name, "summary_all.csv")
```

### Step 2: Run the test and confirm the expected failures

```powershell
Set-Location D:\Data\25_ACE\AG\AG-Research
python -m unittest tests.test_iclr2027_audit -v
```

Expected initial failures: legacy `13 patterns` wording, trained-estimator claim, stale Exp01 summary path.

### Step 3: Implement the minimum audit utility

`iclr2027/audit.py` must expose:

```python
def resolve_exp01_summary() -> Path: ...
def collect_result_inventory(results_dir: Path) -> dict[str, object]: ...
def find_prohibited_claims(text: str) -> list[str]: ...
```

Use it from `validate_results.py`; do not duplicate path selection.

### Step 4: Correct factual wording only

- Replace generic `13 patterns` with `13 multi-agent topologies + solo baseline` where it denotes the entire suite.
- Describe Exp05 as `legacy lexical marginal-utility heuristic`.
- Correct same-model token comparisons.
- Remove claims based on the blank human-evaluation sheet.
- State unequal Exp07 repeat counts explicitly.
- Do not yet insert CATS result numbers.

### Step 5: Re-run audit tests and legacy validation

```powershell
python -m unittest tests.test_iclr2027_audit -v
python validate_results.py
```

Expected: tests pass; validator sees all 14 systems where the source data contains all 14.

---

## Task 2: Add typed research schemas and hash-stable serialization

**Files:**

- Create: `AG/AG-Research/iclr2027/schema.py`
- Create: `AG/AG-Research/iclr2027/io.py`
- Create: `AG/AG-Research/tests/test_iclr2027_schema.py`

### Step 1: Write schema round-trip and rejection tests

Cover:

- public packet contains no `gold_*` or mutation fields;
- PNU is 19 digits;
- program is one of `neighborhood`, `gymnasium`, `cultural`;
- all evidence IDs are unique;
- `program_hash` and `geometry_hash` are nonempty SHA-256 values;
- canonical JSON produces the same SHA-256 regardless of dict insertion order;
- unknown decision values and duplicate evidence IDs fail closed.

### Step 2: Run the failing schema tests

```powershell
python -m unittest tests.test_iclr2027_schema -v
```

### Step 3: Implement dataclasses

Required public interfaces:

```python
@dataclass(frozen=True)
class ArchitectureEvidencePacket:
    case_id: str
    pnu: str
    program: str
    condition: Literal["native", "challenged"]
    execution_id: str
    program_hash: str
    geometry_hash: str
    evidence: tuple[dict[str, Any], ...]

@dataclass(frozen=True)
class ArchitectureGoldRecord:
    case_id: str
    expected_decision: Literal["STOP_ACCEPT", "STOP_REJECT"]
    blocking_issue_codes: tuple[str, ...]
    required_evidence_ids: tuple[str, ...]
    mutation_family: str

@dataclass(frozen=True)
class ArchitectureReviewState:
    checked_domains: tuple[str, ...]
    blocking_issue_codes: tuple[str, ...]
    missing_evidence_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    recommended_decision: Literal["CONTINUE", "STOP_ACCEPT", "STOP_REJECT"]
    confidence: float
```

`io.py` must implement `canonical_json`, `sha256_json`, atomic JSON/JSONL writes, and a public/gold contamination check.

### Step 4: Verify

```powershell
python -m unittest tests.test_iclr2027_schema -v
```

---

## Task 3: Freeze site selection and build native ARR evidence cases

**Files:**

- Create: `AG/AG-Research/iclr2027/site_selection.py`
- Create: `AG/AG-Research/iclr2027/arr_adapter.py`
- Create: `AG/AG-Research/select_iclr2027_sites.py`
- Create: `AG/AG-Research/build_architecture_cases.py`
- Create: `AG/AG-Research/data/iclr2027/site_registry.json`
- Create: `AG/AG-Research/data/iclr2027/split_manifest.json`
- Create: `AG/AG-Research/tests/fixtures/iclr2027/native_summary.json`
- Create: `AG/AG-Research/tests/test_iclr2027_arr_adapter.py`

### Step 1: Write selection and adapter tests

Tests must reject a test PNU when:

- it equals either development PNU;
- its string appears in the 2026-08-18 repository PNU inventory;
- live boundary, law, or parking evidence is absent;
- its parcel-area stratum or district metadata is absent;
- public and gold files share forbidden fields.

The two development sites are fixed:

```python
DEV_PNUS = (
    "1168011800104170004",
    "1168011800104670003",
)
```

### Step 2: Implement deterministic stratified selection

`select_test_sites` must accept a candidate sequence and a fixed seed, then select five sites across three parcel-area bins and at least three administrative districts. Record every exclusion reason and the git commit/hash used for the prior-PNU inventory.

```python
def select_test_sites(
    candidates: Sequence[SiteCandidate],
    *,
    prior_pnus: set[str],
    seed: int = 20260818,
) -> SiteSelectionResult: ...
```

### Step 3: Add the ARR artifact adapter

Read only canonical artifacts produced by `benchmark_maas_book_program_portfolios` and single-execution passports. Required adapter output:

```python
def packet_from_arr_artifacts(
    summary_path: Path,
    *,
    pnu: str,
    program: str,
    case_id: str,
) -> tuple[ArchitectureEvidencePacket, ArchitectureGoldRecord]: ...
```

The adapter must verify execution, program, geometry, and final-legal geometry hashes before returning a packet.

### Step 4: Generate development ARR artifacts

From `ARR/backend`, run the bounded diagnostic target for all three programs and each development PNU:

```powershell
Set-Location D:\Data\25_ACE\ARR\backend
python manage.py benchmark_maas_book_program_portfolios --pnu 1168011800104170004 --program neighborhood --program gymnasium --program cultural --diagnostic-target 3 --output-dir ..\..\..\AG\AG-Research\data\iclr2027\arr\dev-417
python manage.py benchmark_maas_book_program_portfolios --pnu 1168011800104670003 --program neighborhood --program gymnasium --program cultural --diagnostic-target 3 --output-dir ..\..\..\AG\AG-Research\data\iclr2027\arr\dev-467
```

Do not place API keys or full `.env` values in logs.

### Step 5: Select and freeze five new test PNU

```powershell
Set-Location D:\Data\25_ACE\AG\AG-Research
python select_iclr2027_sites.py --candidate-source arr-land-service --count 5 --seed 20260818 --output data\iclr2027\site_registry.json
```

After writing `split_manifest.json`, mark its SHA-256 in `site_registry.json`. From this point, changes require a new manifest version and invalidate prior test results.

### Step 6: Build native cases and verify counts

```powershell
python build_architecture_cases.py --split dev --condition native
python build_architecture_cases.py --split test --condition native
python -m unittest tests.test_iclr2027_arr_adapter -v
```

Expected: 6 native development cases and 15 native frozen-test cases.

---

## Task 4: Implement validated challenged cases without label-only corruption

**Files:**

- Create: `AG/AG-Research/iclr2027/faults.py`
- Create: `AG/AG-Research/iclr2027/validators.py`
- Create: `AG/AG-Research/tests/test_iclr2027_faults.py`
- Modify: `AG/AG-Research/build_architecture_cases.py`

### Step 1: Write one failing test per fault family

Each test must start from a passing native fixture, apply one mutation, rerun the corresponding independent validator, and assert a typed failure:

- `identity.hash_mismatch`
- `law.projection_failed`
- `parking.supply_shortage`
- `program.capacity_failed`
- `geometry.compilation_failed`

Also assert that the public packet contains evidence of the resulting failure but not the mutation family name.

### Step 2: Implement typed mutations and validator registry

```python
FaultFn = Callable[[ArchitectureEvidencePacket], ArchitectureEvidencePacket]

FAULT_REGISTRY: Mapping[str, FaultFn] = {
    "identity_hash": mutate_identity_hash,
    "law_projection": mutate_law_projection,
    "parking_shortage": mutate_parking_shortage,
    "program_capacity": mutate_program_capacity,
    "geometry_compile": mutate_geometry_compile,
}

def validate_terminal_admissibility(
    packet: ArchitectureEvidencePacket,
    state: ArchitectureReviewState,
) -> AdmissibilityResult: ...
```

No mutation function may directly assign the gold decision. The gold decision is derived from the post-mutation validator result.

### Step 3: Deterministically balance fault families

Rotate the five fault families across PNU × program combinations with a stable hash of `case_id`. Confirm that development and test both contain all families.

### Step 4: Build and audit all cases

```powershell
python build_architecture_cases.py --split dev --condition challenged
python build_architecture_cases.py --split test --condition challenged
python build_architecture_cases.py --audit-only
python -m unittest tests.test_iclr2027_faults -v
```

Expected final counts: development 12, frozen test 30; public/gold hash manifest complete; no contamination.

---

## Task 5: Parse agent states and implement deterministic architecture quality

**Files:**

- Create: `AG/AG-Research/iclr2027/review_state.py`
- Create: `AG/AG-Research/iclr2027/architecture_metrics.py`
- Create: `AG/AG-Research/tests/test_iclr2027_review_state.py`
- Create: `AG/AG-Research/tests/test_iclr2027_architecture_metrics.py`

### Step 1: Write parser edge-case tests

Cover valid fenced JSON, multiple blocks, malformed JSON, out-of-range confidence, unknown evidence IDs, duplicate issue codes, handoff-only messages, and adversarial text containing a fake gold field.

The parser must fail closed:

```python
def parse_review_state(text: str) -> ParseResult:
    """Return the last valid ARCH_REVIEW_STATE block or an incomplete state."""
```

### Step 2: Write scorer tests with hand-calculated values

Test exact component scores and total:

```python
quality = (
    0.30 * issue_f1
    + 0.25 * evidence_f1
    + 0.20 * domain_coverage
    + 0.25 * verdict_score
)
```

Unknown citations must reduce precision; incomplete parse must never receive a terminal verdict score.

### Step 3: Implement prefix accumulation

```python
def accumulate_prefix_states(
    turns: Sequence[TurnRecord],
    packet: ArchitectureEvidencePacket,
) -> list[PrefixReviewState]: ...

def score_prefix(
    state: PrefixReviewState,
    gold: ArchitectureGoldRecord,
    packet: ArchitectureEvidencePacket,
) -> ArchitectureTurnScore: ...
```

### Step 4: Verify

```powershell
python -m unittest tests.test_iclr2027_review_state tests.test_iclr2027_architecture_metrics -v
```

---

## Task 6: Add architecture-specific team construction without changing legacy teams

**Files:**

- Create: `AG/AG-Research/iclr2027/architecture_teams.py`
- Create: `AG/AG-Research/iclr2027/prompts.py`
- Create: `AG/AG-Research/tests/test_iclr2027_architecture_teams.py`
- Modify: `AG/AG-Research/experiment_utils.py`

### Step 1: Add a failing runner-injection test

`ExperimentRunner.run_batch` must accept a team builder without altering default behavior:

```python
TeamBuilder = Callable[[str, int | None], Any]

async def run_batch(
    ...,
    team_builder: TeamBuilder | None = None,
) -> list[RunResult]: ...
```

When `team_builder is None`, the method must still call `TeamFactory.build` and reproduce legacy output.

### Step 2: Implement `ArchitectureTeamFactory`

```python
class ArchitectureTeamFactory:
    @staticmethod
    def build(pattern: str, max_messages: int | None = None, model: str | None = None): ...
```

Requirements:

- support all 14 system IDs;
- preserve the original topology class and participant count;
- replace generic business/research roles with architecture disciplines;
- require exactly one `ARCH_REVIEW_STATE` block per substantive message;
- use `TERMINATE` only as a reported signal; the natural topology termination condition remains recorded;
- keep `rr3`, `sel3`, `swm3`, `refl3`, `debate3` on the identical three-role bank.

### Step 3: Test topology parity

For all pattern IDs, compare legacy and architecture factories on team type, participant count, max-message budget, and composed-stage count. No API call is needed.

### Step 4: Verify the entire legacy runner still imports

```powershell
python -m unittest tests.test_iclr2027_architecture_teams -v
python -c "from experiment_utils import TeamFactory, ExperimentRunner; print(len(__import__('config').PATTERNS_ALL))"
```

Expected output includes `14`.

---

## Task 7: Build the Exp08 runner, execute the 180-run pilot, and enforce the gate

**Files:**

- Create: `AG/AG-Research/run_exp08_architecture.py`
- Create: `AG/AG-Research/iclr2027/pilot_gate.py`
- Create: `AG/AG-Research/tests/test_iclr2027_pilot_gate.py`
- Output: `AG/AG-Research/results/exp08_architecture/pilot/`

### Step 1: Test dry-run matrix and resume keys

Dry run must produce exactly:

`5 patterns × 12 cases × 3 repeats = 180 planned runs`

Resume identity must include `case_id`, `pattern`, `repeat`, `model`, packet SHA-256, prompt SHA-256, and code commit.

### Step 2: Implement the runner CLI

```powershell
python run_exp08_architecture.py --split dev --patterns rr3 sel3 swm3 refl3 debate3 --repeats 3 --model claude-haiku-4-5-20251001 --checkpoint-dir results\exp08_architecture\planning --dry-run
```

Artifacts per run:

- raw trajectory JSONL
- parsed turn-state JSONL
- deterministic turn-score CSV
- errors/retries JSONL
- model/prompt/packet manifest
- atomic per-run transaction ledger plus recoverable derived checkpoint

### Step 3: Run one-case smoke test

```powershell
python run_exp08_architecture.py --split dev --patterns rr3 --repeats 1 --limit-cases 1 --checkpoint-dir results\exp08_architecture\smoke_rr3 --confirm-paid-run --estimated-cost-per-run-usd <estimate> --estimated-completion-date 2026-08-21
```

Confirm no gold fields occur in the captured prompt.

### Step 4: Execute the pilot

```powershell
python run_exp08_architecture.py --split dev --patterns rr3 sel3 swm3 refl3 debate3 --repeats 3 --model claude-haiku-4-5-20251001 --checkpoint-dir results\exp08_architecture\pilot --confirm-paid-run --estimated-cost-per-run-usd <estimate> --estimated-completion-date 2026-08-24
```

### Step 5: Evaluate the pilot gate

```powershell
python -m iclr2027.pilot_gate --results results\exp08_architecture\pilot --output results\exp08_architecture\pilot_gate.json
```

Hard gate before further spending:

- parse success ≥ 95%;
- run error < 5%;
- gold safe/unsafe each 30–70%;
- all five fault families reproduced;
- estimated primary completion by 2026-09-02;
- estimated total cost explicitly printed.

Do not run Task 11 if this gate is false.

---

## Task 8: Extract leakage-free trajectory states and future-benefit labels

**Files:**

- Create: `AG/AG-Research/iclr2027/trajectory_features.py`
- Create: `AG/AG-Research/build_exp09_dataset.py`
- Create: `AG/AG-Research/tests/test_iclr2027_trajectory_features.py`
- Output: `AG/AG-Research/results/exp09_cats/dataset/`

### Step 1: Write temporal leakage tests

For every state at turn `t`, perturb turns `t+1...T` and assert the feature vector is unchanged. Assert that `quality`, `future_max_quality`, `label`, gold issue codes, and mutation family are absent from the feature columns.

### Step 2: Implement feature extraction

Use train-fitted `TfidfVectorizer` to produce only scalar prefix distances; do not append sparse text vectors to the classifier. Required output columns include:

```text
domain, trajectory_id, group_id, turn_index, normalized_turn,
pattern, pattern_category, agent_count, speaker_count,
turn_tokens, cumulative_tokens, token_delta_1, token_delta_2,
word_count, unique_ratio, repeated_ngram_ratio,
tfidf_distance_prev, tfidf_distance_prefix,
reported_confidence, parsed_completeness,
geometry_status, law_status, parking_status, program_status,
quality_t, future_max_quality, beneficial_future
```

The last three are label-side columns and must be removed before model fitting.

### Step 3: Normalize quality consistently

- general Exp02 score: `(overall - 1) / 4`
- architecture score: already `[0,1]`
- `beneficial_future = future_max_quality - quality_t > 0.02`

### Step 4: Build deterministic splits

- General: hash-split by `task_id`, never by turn.
- Architecture train: development PNU `1168011800104170004`.
- Architecture calibration: development PNU `1168011800104670003`.
- Architecture test: five frozen PNU; do not read test files during this task.

### Step 5: Build and audit dataset

```powershell
python build_exp09_dataset.py --general results\exp02 --architecture results\exp08_architecture\pilot --epsilon 0.02 --output results\exp09_cats\dataset
python -m unittest tests.test_iclr2027_trajectory_features -v
```

Write `feature_manifest.json` with source hashes, split counts, class balance, vectorizer vocabulary hash, and forbidden-column audit.

---

## Task 9: Implement CATS classifier and trajectory-level conformal calibration

**Files:**

- Create: `AG/AG-Research/iclr2027/cats.py`
- Create: `AG/AG-Research/train_exp09_cats.py`
- Create: `AG/AG-Research/tests/test_iclr2027_cats.py`
- Output: `AG/AG-Research/results/exp09_cats/models/`

### Step 1: Write exact finite-sample calibration tests

Cover quantile rank, no-positive trajectory behavior, repeated-turn sequential risk, `patience=2`, hard-guard override, and deterministic model serialization.

Primary calibration implementation:

```python
def trajectory_nonconformity(rows: pd.DataFrame) -> float:
    positive = rows.loc[rows["beneficial_future"] == 1, "p_improve"]
    return 0.0 if positive.empty else float((1.0 - positive).max())

def finite_sample_quantile(scores: np.ndarray, alpha: float) -> float:
    rank = math.ceil((len(scores) + 1) * (1.0 - alpha))
    if rank > len(scores):
        return math.inf
    return float(np.partition(scores, rank - 1)[rank - 1])
```

### Step 2: Implement models

- `LogisticRegression` baseline with standardized numeric features and one-hot categorical features.
- `HistGradientBoostingClassifier` primary with the same frozen preprocessing contract.
- fixed random seed `20260818`.
- model artifact includes feature order, train-source hashes, scikit-learn version, `ε`, `α`, quantile, and calibration trajectory IDs.

### Step 3: Implement stop policy

```python
class CATSStopPolicy:
    def observe(self, state: RuntimeState) -> StopDecision:
        no_gain = (1.0 - self.predict_improvement(state)) > self.q_alpha
        safe = self.admissibility_guard(state)
        self.streak = self.streak + 1 if no_gain and safe else 0
        return StopDecision(stop=self.streak >= 2, reason="cats" if self.streak >= 2 else "continue")
```

### Step 4: Train without frozen test access

```powershell
python train_exp09_cats.py --dataset results\exp09_cats\dataset --alpha 0.10 --model histgb --output results\exp09_cats\models\cats-primary.joblib
python train_exp09_cats.py --dataset results\exp09_cats\dataset --alpha 0.10 --model logistic --output results\exp09_cats\models\cats-logistic.joblib
```

### Step 5: Run tests and inspect development calibration

```powershell
python -m unittest tests.test_iclr2027_cats -v
python train_exp09_cats.py --dataset results\exp09_cats\dataset --report-only
```

Freeze model and calibration artifact hashes before Task 11.

---

## Task 10: Implement offline policy replay and online parity validation

**Files:**

- Create: `AG/AG-Research/iclr2027/policy_replay.py`
- Create: `AG/AG-Research/replay_exp09_policies.py`
- Create: `AG/AG-Research/tests/test_iclr2027_policy_replay.py`
- Output: `AG/AG-Research/results/exp09_cats/replay/`

### Step 1: Write synthetic trajectory tests

Hand-construct plateau, late-improvement, oscillation, unsafe-pass, and malformed-state trajectories. Assert exact stop turn, stopped quality, token sum, overshoot, regret, and unsafe flag for every policy.

### Step 2: Implement the policy registry

```python
POLICIES = {
    "natural": NaturalStopPolicy,
    "max_cap": MaxCapPolicy,
    "keyword": KeywordPolicy,
    "lexical_du": LegacyDeltaUPolicy,
    "semantic_patience": SemanticPatiencePolicy,
    "logistic": LearnedPolicy,
    "uncalibrated": LearnedPolicy,
    "state_conformal": StateConformalPolicy,
    "cats": CATSStopPolicy,
    "cats_no_guard": CATSStopPolicy,
    "oracle": OraclePeakPolicy,
}
```

All policies return a common `ReplayOutcome`; only oracle may access future quality.

### Step 3: Replay development trajectories

```powershell
python replay_exp09_policies.py --trajectories results\exp08_architecture\pilot --models results\exp09_cats\models --split dev --output results\exp09_cats\replay\dev
```

### Step 4: Enforce the CATS development gate

Continue only if CATS achieves:

- median token reduction ≥ 15%;
- mean quality-difference 95% cluster-bootstrap lower bound > -0.03;
- no observed unsafe stop on development;
- empirical trajectory coverage reported, not silently assumed.

### Step 5: Verify online/offline parity on 20 preselected development trajectories

```powershell
python run_exp08_architecture.py --split dev --online-policy results\exp09_cats\models\cats-primary.joblib --parity-sample 20 --output results\exp09_cats\parity
```

For every sample, prefix message hashes and cumulative tokens must match through the chosen stop turn. Investigate any mismatch before primary runs.

---

## Task 11: Execute frozen primary, cross-model, and canonical ARR baselines

**Files:**

- Modify: `AG/AG-Research/run_exp08_architecture.py`
- Create: `AG/AG-Research/run_iclr2027_experiment_matrix.py`
- Output: `AG/AG-Research/results/exp08_architecture/primary/`
- Output: `AG/AG-Research/results/exp08_architecture/cross_model_gpt54/`
- Output: `AG/AG-Research/results/exp08_architecture/arr_fixed_flow/`

### Step 1: Print and manually verify the frozen matrix

```powershell
python run_iclr2027_experiment_matrix.py --dry-run
```

Expected exact counts:

- primary Haiku: `14 × 30 × 3 = 1,260`
- cross-model GPT-5.4: `5 × 30 × 2 = 300`
- canonical ARR fixed-flow: `30 deterministic cases × 1 = 30`
- pilot plus final: `1,770 total new runs`

### Step 2: Execute primary with append-only checkpoints

```powershell
python run_iclr2027_experiment_matrix.py --stage primary --model claude-haiku-4-5-20251001 --resume
```

Never delete a failed row. Record retry lineage and report both first-attempt and eventual-success rates.

### Step 3: Execute cross-model

```powershell
python run_iclr2027_experiment_matrix.py --stage cross-model --model gpt-5.4 --patterns rr3 sel3 swm3 refl3 debate3 --resume
```

### Step 4: Execute canonical ARR baseline

```powershell
python run_iclr2027_experiment_matrix.py --stage arr-fixed-flow --resume
```

The ARR fixed-flow baseline is reported for verdict/constraint correctness, not as a directly fair conversational-token baseline.

### Step 5: Freeze raw results

Write `results_manifest.json` containing every file hash, row count, planned/missing key, model version, date, prompt hash, packet hash, and retry lineage. No analysis code may mutate raw files.

---

## Task 12: Run final replay, statistics, ablations, and figures

**Files:**

- Create: `AG/AG-Research/iclr2027/statistics.py`
- Create: `AG/AG-Research/analyze_iclr2027.py`
- Create: `AG/AG-Research/tests/test_iclr2027_statistics.py`
- Output: `AG/AG-Research/results/iclr2027_analysis/`
- Output: `AG/AG-Research/figures/iclr2027_*.pdf`
- Output: `AG/AG-Research/tables/iclr2027_*.tex`

### Step 1: Test statistical functions against known small arrays

Implement and test:

```python
def paired_cluster_bootstrap(..., clusters: str, n_resamples: int = 10_000, seed: int = 20260818): ...
def holm_adjust(p_values: Sequence[float]) -> np.ndarray: ...
def wilson_interval(successes: int, total: int, confidence: float = 0.95): ...
def expected_calibration_error(y: np.ndarray, p: np.ndarray, bins: int = 10): ...
```

### Step 2: Replay all frozen trajectories once

```powershell
python replay_exp09_policies.py --trajectories results\exp08_architecture\primary --models results\exp09_cats\models --split test --output results\exp09_cats\replay\test
python replay_exp09_policies.py --trajectories results\exp08_architecture\cross_model_gpt54 --models results\exp09_cats\models --split test-model --output results\exp09_cats\replay\gpt54
```

### Step 3: Produce primary tables

Required tables:

1. natural topology cost/quality/termination outcomes;
2. policy quality, tokens, unsafe stops, overshoot, regret;
3. native vs challenged and five fault families;
4. held-out PNU/program/model coverage;
5. controlled three-agent subset;
6. ablations and `ε`/`α` sensitivity.

### Step 4: Produce exactly four main figures

```powershell
python analyze_iclr2027.py --manifest results\exp08_architecture\results_manifest.json --output results\iclr2027_analysis --figures figures --tables tables
```

Figures:

- CATS architecture diagram;
- quality–token Pareto;
- natural vs CATS stop turn by topology;
- architecture unsafe-stop/calibration by condition.

### Step 5: Evaluate the paper success gate without changing it

Write `submission_gate.json` with pass/fail for:

- median token reduction ≥ 20%;
- mean `ΔQ` 95% CI lower bound > -0.02;
- zero observed CATS unsafe stops on frozen architecture test;
- consistent direction in at least three topology categories;
- no held-out-model quality-margin violation.

Report failures as results; never change the threshold after seeing test data.

---

## Task 13: Rewrite the paper around three claims and fit the ICLR format

**Files:**

- Preserve as legacy: `AG/AG-Research/latex/main.tex`
- Download and extract from the official archive: `https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip`
- Extract official files under: `AG/AG-Research/latex/iclr2027/`
- Create from `iclr2027_conference.tex`: `AG/AG-Research/latex/iclr2027/main.tex`
- Create: `AG/AG-Research/latex/iclr2027/references.bib`
- Create: `AG/AG-Research/latex/iclr2027/contributions.tex`
- Create: `AG/AG-Research/latex/iclr2027/method.tex`
- Create: `AG/AG-Research/latex/iclr2027/architecture.tex`
- Create: `AG/AG-Research/latex/iclr2027/results.tex`
- Create: `AG/AG-Research/latex/iclr2027/ai_use.tex`
- Create: `AG/AG-Research/latex/iclr2027/reproducibility.tex`
- Create: `AG/AG-Research/latex/iclr2027/check_pages.py`
- Create: `AG/AG-Research/CLAIM_EVIDENCE_MATRIX.md`

### Step 0: Replace the COLM wrapper with the official ICLR 2027 wrapper

Download the style archive from the URL published in the ICLR 2027 Author Guidelines, record its SHA-256, and extract all seven official files into `latex/iclr2027/`: `iclr2027_conference.tex`, `iclr2027_conference.sty`, `iclr2027_conference.bst`, `iclr2027_conference.bib`, `math_commands.tex`, `fancyhdr.sty`, and `natbib.sty`. Do not rename the existing COLM `main.tex` into an ICLR paper or reuse `colm2026_conference.sty`.

The new `latex/iclr2027/main.tex` must derive from the official sample, load the official style in anonymous submission mode, and include the method/result section files listed above.

### Step 1: Create a claim-to-artifact matrix before prose

Every abstract, introduction, and conclusion number must point to:

- source CSV/JSON;
- analysis function;
- table/figure;
- sample size and model;
- confidence interval.

Unsupported superlatives such as “largest” and “first” require a documented literature basis or removal.

### Step 2: Rewrite the abstract last

The body order is:

1. empirical termination problem;
2. CATS method;
3. general-domain results;
4. architecture hard-constraint results;
5. calibration/OOD/ablation;
6. limitations.

Move the legacy 39 findings, full topology tables, all prompts, extra model tables, and fault details to the appendix.

### Step 3: Use accepted-work comparisons accurately

Related work must distinguish:

- GraphPlanner/CARD: routing/topology selection;
- Stop Wasting Your Tokens: heuristic supervisor;
- ZIP-RC/Learning How Hard to Think: adaptive test-time compute;
- MAC-AMP: multi-agent engineering loop;
- SymPoint/cadrille/CinDM: objective CAD/engineering validation.

Do not imply reviewer statements when only paper limitations/results were inspected.

### Step 4: State limitations plainly

- conformal coverage is marginal and exchangeability-dependent;
- only five new test sites and three programs;
- fault injection complements but does not replace naturally occurring failures;
- architecture benchmark evaluates review/termination, not aesthetic design quality;
- CATS only truncates a natural trajectory and cannot repair a naturally premature legacy stop.

### Step 5: Compile and enforce page budget

```powershell
Set-Location D:\Data\25_ACE\AG\AG-Research\latex\iclr2027
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
python check_pages.py main.pdf
```

Expected: 9 main-text pages under the official ICLR 2027 template; references and appendix follow it. Include the required AI-use statement and the recommended reproducibility statement in the template-sanctioned positions; both are checked against the current Author Guidelines.

---

## Task 14: Build the anonymous reproducibility package and run final verification

**Files:**

- Create: `AG/AG-Research/REPRODUCIBILITY_ICLR2027.md`
- Create: `AG/AG-Research/reproduce_iclr2027.py`
- Create: `AG/AG-Research/check_anonymity.py`
- Create: `AG/AG-Research/tests/test_iclr2027_reproducibility.py`
- Create: `AG/AG-Research/results/iclr2027_release_manifest.json`

### Step 1: Add a one-command read-only reproduction entry point

```powershell
python reproduce_iclr2027.py --verify-manifests --replay-policies --rebuild-tables --rebuild-figures
```

The command must never call paid APIs unless `--allow-api-calls` is explicitly passed.

### Step 2: Run all tests

```powershell
Set-Location D:\Data\25_ACE\AG\AG-Research
python -m unittest discover -s tests -p "test_iclr2027_*.py" -v
```

### Step 3: Run result completeness and leakage audits

```powershell
python validate_results.py
python build_architecture_cases.py --audit-only
python reproduce_iclr2027.py --verify-manifests --replay-policies --rebuild-tables --rebuild-figures
python check_anonymity.py latex\iclr2027\main.tex REPRODUCIBILITY_ICLR2027.md
```

### Step 4: Verify paper artifact

Confirm:

- no author identity, local username, API key, absolute private path, or institution leak;
- every main claim exists in `CLAIM_EVIDENCE_MATRIX.md`;
- raw result hashes match release manifest;
- all 30 frozen cases and planned run keys are accounted for;
- failed/retried runs are disclosed;
- AI-use statement follows ICLR 2027 rules;
- abstract and paper are ready by 2026-09-18 and 2026-09-25 AoE respectively.

### Step 5: Stop condition

Implementation is complete only when tests, manifests, paper compilation, anonymity check, and claim-evidence audit all pass. A positive `submission_gate.json` supports the strong CATS claim; a negative gate requires honest claim reduction, not more test tuning.

---

## Execution order and dates

| Dates | Tasks | Exit condition |
|---|---|---|
| Aug 19–21 | 1–6 | schemas, five new sites, 30 frozen cases, topology parity |
| Aug 22–24 | 7 | pilot gate decision |
| Aug 25–28 | 8–10 | frozen CATS artifact and online parity |
| Aug 29–Sep 6 | 11–12 | complete primary/cross-model results and submission gate |
| Sep 7–17 | 13–14 | 9-page anonymous reproducible paper |
| Sep 18 | abstract | official abstract submission |
| Sep 25 | paper | official paper submission |

## First execution checkpoint

Execute Tasks 1–7 first, then stop for a pilot review. Do not pre-author result claims or spend on the 1,260-run primary matrix before the pilot gate report is available.
