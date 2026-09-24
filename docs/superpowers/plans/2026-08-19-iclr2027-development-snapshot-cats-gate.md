# ICLR 2027 Development Snapshot and CATS Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the completed 450-run v12 development collection into a receipt-bound, leakage-safe CATS model and an offline development-gate result without reading held-out artifacts or making another LLM call.

**Architecture:** Treat `pilot_full_v12_clean_recovery/run_transactions/` as the immutable source and build disposable artifacts in `results/exp09_cats/`. A read-only ingest layer validates and receipts all 450 transactions; a site-grouped dataset layer physically separates prefix-only runtime features, private labels, and assignments; model and replay layers consume only their declared artifact schemas. A negative legacy pilot gate remains binding, so this plan can produce only a method-lock candidate that blocks held-out access.

**Tech Stack:** Python 3.13, `unittest`, dataclasses, canonical JSON/JSONL, SHA-256, pandas 2.3, NumPy 2.4, scikit-learn 1.7, joblib 1.5.

**Spec:** `docs/superpowers/specs/2026-08-19-iclr2027-option-b-design.md`

## Global Constraints

- Preserve the exact v12 transaction set SHA-256 `3e7e9c0edd5fc8b1f2cc77f69da6dca9e381018d117a2cf3e8e6a4e94459de74`, run-plan SHA-256 `7672205a2cdbf8f5b5c929744e58d31c086e7765cb166a80a9a17f59f458b7c9`, and code/runtime identity `179fe49607a33e2eca5337bb099cde78be96055b-dirty-89d4ae988d18b5c7-deps-48d730d98a916537`.
- Do not modify `results/exp08_architecture/pilot_full_v12_clean_recovery/run_transactions/`; raw transactions are append-only and derived ledgers are reproducible.
- Do not open or enumerate `test.*` case bundles, run a test split, fit on held-out topology/model data, or call an LLM in this plan.
- Freeze `epsilon=0.02`, `alpha=0.10`, `patience=2`, primary model `histgb`, sensitivity model `logistic`, epsilon sensitivities `{0.01, 0.05}`, alpha sensitivities `{0.05, 0.20}`, and seed `20260819`.
- Use opaque public `site_ref` as the indivisible group. Rank the five development sites by `SHA256("20260819\0" + site_ref)` and assign ranks 0–1 to train, rank 2 to calibration, and ranks 3–4 to development gate. This 2/1/2 allocation preserves every site while retaining two independent development-gate sites for the frozen cluster bootstrap.
- Every native/challenged condition, program/case family, topology, and repeat from one site remains in one partition.
- Runtime feature files contain no quality, future, gold issue, private condition, mutation, raw PNU, internal ID, final trajectory length, final token count, or final outcome fields.
- Private label files contain only opaque row identity, `quality_t`, `future_max_quality`, and `beneficial_future`; assignment/census data live in a third physical artifact.
- Fit TF-IDF vocabulary, imputers, encoders, scalers, and classifiers on train sites only. Calibration and development-gate rows are transform-only.
- A terminal prefix has `future_max_quality = quality_t` and `beneficial_future = false`; no empty maximum or look-ahead feature enters runtime data.
- Replay only selects an existing agent-turn prefix and must reproduce exact source message hashes and cumulative visible-agent token counts through that turn.
- Missing selector/control/cached-token/cost events block invoice-grade cost and total-compute claims. Report visible-agent token effects with their exact boundary.
- The existing `pilot_gate.json` is negative. No positive method-lock or held-out access receipt may be emitted by this plan, even if the CATS development gate passes.
- Do not commit, push, publish, or run new paid model traffic without explicit user authorization.

---

### Task 1: Freeze the study contract and canonical receipt primitives

**Files:**
- Create: `AG/AG-Research/iclr2027/study_contract.py`
- Create: `AG/AG-Research/iclr2027/artifact_receipts.py`
- Create: `AG/AG-Research/tests/test_iclr2027_study_contract.py`
- Create: `AG/AG-Research/tests/test_iclr2027_artifact_receipts.py`

**Interfaces:**
- Consumes: no data files; all values are constants from the approved Option B spec and the global constraints above.
- Produces: `StudyContract`, `canonical_artifact_receipt(...)`, `verify_artifact_receipt(...)`, and canonical row/file-set hashing used by every later task.

- [ ] **Step 1: Write failing tests for the exact frozen contract**

```python
def test_primary_contract_is_exact_and_immutable():
    contract = StudyContract.primary()
    self.assertEqual(contract.epsilon, 0.02)
    self.assertEqual(contract.alpha, 0.10)
    self.assertEqual(contract.patience, 2)
    self.assertEqual(contract.group_seed, 20260819)
    self.assertEqual(contract.site_partition_counts, (2, 1, 2))
    self.assertEqual(contract.epsilon_sensitivity, (0.01, 0.05))
    self.assertEqual(contract.alpha_sensitivity, (0.05, 0.20))
```

- [ ] **Step 2: Write failing receipt tamper tests**

```python
def test_receipt_rejects_changed_file_or_row_census():
    receipt = canonical_artifact_receipt(
        schema_version="ace.iclr2027.test_receipt.v1",
        files={"a.json": self.file_a},
        row_census={"rows": 2},
        bindings={"source": "a" * 64},
    )
    self.file_a.write_text("changed", encoding="utf-8")
    with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
        verify_artifact_receipt(receipt, root=self.root)
```

- [ ] **Step 3: Run the focused tests and verify RED**

Run:

```powershell
python -m unittest tests.test_iclr2027_study_contract tests.test_iclr2027_artifact_receipts -v
```

Expected: import failure because both modules are absent.

- [ ] **Step 4: Implement immutable contract and receipt schemas**

```python
@dataclass(frozen=True)
class StudyContract:
    epsilon: float
    alpha: float
    patience: int
    group_seed: int
    site_partition_counts: tuple[int, int, int]
    epsilon_sensitivity: tuple[float, ...]
    alpha_sensitivity: tuple[float, ...]

    @classmethod
    def primary(cls) -> "StudyContract":
        return cls(0.02, 0.10, 2, 20260819, (2, 1, 2), (0.01, 0.05), (0.05, 0.20))
```

`artifact_receipts.py` must canonicalize sorted relative paths, hash raw bytes, require lowercase 64-character SHA-256 bindings, reject symlinks and paths outside the supplied root, and verify exact file and row-census keys.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run the command from Step 3. Expected: all tests pass.

- [ ] **Step 6: Run Ruff and compile checks**

```powershell
python -m ruff check iclr2027/study_contract.py iclr2027/artifact_receipts.py tests/test_iclr2027_study_contract.py tests/test_iclr2027_artifact_receipts.py
python -m compileall -q iclr2027/study_contract.py iclr2027/artifact_receipts.py
```

Expected: both commands exit 0.

### Task 2: Validate and freeze the 450-transaction development snapshot

**Files:**
- Modify: `AG/AG-Research/iclr2027/exp08.py`
- Create: `AG/AG-Research/iclr2027/trajectory_ingest.py`
- Create: `AG/AG-Research/freeze_iclr2027_development.py`
- Create: `AG/AG-Research/tests/test_iclr2027_trajectory_ingest.py`
- Output: `AG/AG-Research/results/exp09_cats/development_snapshot/snapshot_receipt.json`

**Interfaces:**
- Consumes: the v12 result directory, `StudyContract`, and receipt primitives.
- Produces: `load_validated_transactions(results_dir) -> tuple[Mapping[str, Any], ...]`, `DevelopmentSnapshot`, and `ace.iclr2027.development_snapshot_receipt.v1`.

- [ ] **Step 1: Add failing read-only ingest and tamper tests**

```python
def test_snapshot_requires_exact_450_completed_transactions():
    snapshot = load_development_snapshot(self.v12, expected_count=450)
    self.assertEqual(len(snapshot.transactions), 450)
    self.assertEqual(snapshot.transaction_set_sha256, EXPECTED_TRANSACTION_SET)
    self.assertEqual(snapshot.final_parse_complete_count, 450)
    self.assertEqual(snapshot.terminal_error_count, 0)

def test_snapshot_rejects_message_or_manifest_tamper():
    clone = copy_fixture(self.v12)
    mutate_one_message(clone)
    with self.assertRaises(ValueError):
        load_development_snapshot(clone, expected_count=450)
```

- [ ] **Step 2: Run the focused test and verify RED**

```powershell
python -m unittest tests.test_iclr2027_trajectory_ingest -v
```

Expected: missing `trajectory_ingest` API.

- [ ] **Step 3: Expose one read-only transaction loader without duplicating validation**

Refactor `exp08.py` so both ledger materialization and snapshot ingest call:

```python
def load_validated_transactions(output_dir: Path) -> tuple[Mapping[str, Any], ...]:
    transaction_dir = output_dir / "run_transactions"
    rows = []
    for path in sorted(transaction_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.append(_validate_transaction(payload, expected_resume_key=path.stem))
    return tuple(rows)
```

Keep `_materialize_transactions()` as the only writer of derived Exp08 ledgers; it delegates its read/validation step to this function.

- [ ] **Step 4: Implement strict snapshot recomputation**

`trajectory_ingest.py` must verify the run manifest, exact run plan identities, exact 450-key equality, the expected v12 commitments, 450 completed checkpoints, zero terminal errors, 450 final parse-complete states, all nested identity bindings, and every persisted semantic score through the existing Exp08 validation path. Compute a SHA-256 for each agent message from canonical `{index, source, content, tokens_in, tokens_out}` and bind the ordered per-trajectory message-hash list in the receipt.

- [ ] **Step 5: Implement an atomic freeze CLI**

```powershell
python freeze_iclr2027_development.py --results results/exp08_architecture/pilot_full_v12_clean_recovery --pilot-gate results/exp08_architecture/pilot_full_v12_clean_recovery/pilot_gate.json --output results/exp09_cats/development_snapshot/snapshot_receipt.json
```

The CLI must fail on output collision unless existing bytes are identical. It writes no file inside the v12 result directory.

- [ ] **Step 6: Run tests and freeze the real snapshot**

Run the test from Step 2, then the CLI from Step 5. Expected receipt values include `transaction_count=450`, `terminal_error_count=0`, `final_parse_complete_count=450`, and the three frozen hashes from Global Constraints.

- [ ] **Step 7: Re-run the exact 450-key no-op verifier**

```powershell
python run_exp08_architecture.py --split dev --patterns rr3 sel3 swm3 refl3 debate3 --repeats 3 --model claude-haiku-4-5-20251001 --checkpoint-dir results/exp08_architecture/pilot_full_v12_clean_recovery --confirm-paid-run --estimated-cost-per-run-usd 0.0 --estimated-completion-date 2026-08-20
```

Expected: `completed_runs_this_invocation=0`, `skipped_runs=450`.

### Task 3: Build site-group assignments and physically separated prefix artifacts

**Files:**
- Create: `AG/AG-Research/iclr2027/trajectory_features.py`
- Create: `AG/AG-Research/build_exp09_dataset.py`
- Create: `AG/AG-Research/tests/test_iclr2027_trajectory_features.py`
- Modify: `AG/AG-Research/iclr2027/validators.py`
- Test: `AG/AG-Research/tests/test_iclr2027_validators.py`
- Output: `AG/AG-Research/results/exp09_cats/dataset/runtime/runtime_features.jsonl`
- Output: `AG/AG-Research/results/exp09_cats/dataset/private/private_labels.jsonl`
- Output: `AG/AG-Research/results/exp09_cats/dataset/private/group_assignments.json`
- Output: `AG/AG-Research/results/exp09_cats/dataset/feature_manifest.json`

**Interfaces:**
- Consumes: verified `DevelopmentSnapshot`, development native/challenged public/internal/gold bundles, and `StudyContract`.
- Produces: `assign_site_groups(...)`, `PrefixRuntimeFeature`, `PrivatePrefixLabel`, `DatasetManifest`, and a public-case-compatible `validate_terminal_admissibility(...)` path for the CATS hard guard.

- [ ] **Step 1: Write group-integrity and test-access RED tests**

```python
def test_five_sites_are_assigned_two_one_two_without_crossing():
    assignments = assign_site_groups(self.dev_case_index, seed=20260819)
    self.assertEqual(Counter(a.partition for a in assignments), {"train": 2, "calibration": 1, "development_gate": 2})
    by_site = defaultdict(set)
    for row in assignments:
        by_site[row.site_ref].add(row.partition)
    self.assertTrue(all(len(partitions) == 1 for partitions in by_site.values()))

def test_builder_rejects_any_test_bundle_argument_before_method_lock():
    with self.assertRaisesRegex(PermissionError, "held-out access is locked"):
        build_dataset(case_paths=[Path("data/iclr2027/cases/test.native.public.jsonl")], method_lock=None)
```

- [ ] **Step 2: Write future/private perturbation and forbidden-field tests**

```python
def test_runtime_prefix_is_invariant_to_future_and_private_changes():
    left = runtime_features(prefix_fixture(), fitted=self.transformer)
    changed = mutate_future_turns_and_private_gold(prefix_fixture())
    right = runtime_features(changed, fitted=self.transformer)
    self.assertEqual(canonical_json(left), canonical_json(right))

def test_runtime_schema_excludes_forbidden_fields():
    forbidden = {"quality_t", "future_max_quality", "beneficial_future", "condition", "mutation_family", "pnu", "gold", "final_turn_count", "final_tokens"}
    self.assertFalse(forbidden & set(PrefixRuntimeFeature.field_names()))
```

- [ ] **Step 3: Run focused tests and verify RED**

```powershell
python -m unittest tests.test_iclr2027_trajectory_features tests.test_iclr2027_validators -v
```

- [ ] **Step 4: Generalize terminal admissibility to the public case schema**

Refactor the validator core to accept either the private `ArchitectureEvidencePacket` identity (`pnu`) or public `ArchitecturePublicCase` identity (`site_ref`) without changing issue rules. Add a parity test asserting public and private projections return identical decision, blocking, missing-evidence, and admissibility results for all 30 development cases.

- [ ] **Step 5: Implement the exact runtime feature schema**

Persist these model columns only:

```python
NUMERIC_FEATURES = (
    "turn_index", "normalized_turn", "agent_count", "speaker_count",
    "turn_tokens", "cumulative_tokens", "token_delta_1", "token_delta_2",
    "word_count", "unique_ratio", "repeated_ngram_ratio",
    "tfidf_distance_prev", "tfidf_distance_prefix",
    "reported_confidence", "checked_domain_count", "evidence_count",
    "blocking_issue_count", "missing_evidence_count",
)
CATEGORICAL_FEATURES = (
    "pattern", "pattern_category", "source", "recommended_decision",
    "parse_complete", "site_evidence_present", "geometry_evidence_present",
    "law_evidence_present", "parking_evidence_present", "program_evidence_present",
)
```

Identifiers `row_id` and `trajectory_id` are persisted but excluded from `MODEL_FEATURES`. Compute `normalized_turn` as one-based agent turn divided by the registered topology budget `PATTERN_MAX_MESSAGES[pattern]`, never by observed final length.

- [ ] **Step 6: Fit text distance on train sites only**

Use `TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1, norm="l2")`. Its `fit` method receives only train-site turn text. Transform calibration and development-gate text without refitting; persist only the two scalar cosine distances and a vocabulary SHA-256, never raw text.

- [ ] **Step 7: Materialize private labels and assignments separately**

For each prefix row `t`, compute:

```python
future_max = max(qualities[t + 1 :], default=qualities[t])
label = future_max - qualities[t] > epsilon
```

Write labels sorted by opaque `row_id`. Write assignments sorted by opaque `trajectory_id` with `group_id`, partition, and private census fields. Verify 1:1 row-ID equality between runtime and private label files without combining their columns on disk.

- [ ] **Step 8: Run the development-only dataset CLI**

```powershell
python build_exp09_dataset.py --snapshot results/exp09_cats/development_snapshot/snapshot_receipt.json --results results/exp08_architecture/pilot_full_v12_clean_recovery --split-manifest data/iclr2027/split_manifest.json --projection-identity data/iclr2027/projection_identity.private.json --epsilon 0.02 --output results/exp09_cats/dataset
```

Expected: five site groups allocated 2/1/2, 450 trajectories assigned once, no test bundle read, and a feature manifest binding all three separated artifacts and their censuses.

### Task 4: Build event-based usage accounting and claim availability

**Files:**
- Create: `AG/AG-Research/iclr2027/usage_ledger.py`
- Create: `AG/AG-Research/tests/test_iclr2027_usage_ledger.py`
- Modify: `AG/AG-Research/build_exp09_dataset.py`
- Output: `AG/AG-Research/results/exp09_cats/dataset/usage/usage_events.jsonl`
- Output: `AG/AG-Research/results/exp09_cats/dataset/usage/claim_availability.json`

**Interfaces:**
- Consumes: validated transaction raw turns and error lineage.
- Produces: `UsageEvent`, `UsageAvailability`, and cumulative visible-agent usage indexed by `(trajectory_id, turn_index)`.

- [ ] **Step 1: Write failing event and claim-boundary tests**

```python
def test_missing_selector_and_control_usage_blocks_cost_claims():
    availability = summarize_usage(self.v12_transactions)
    self.assertTrue(availability.visible_agent_tokens)
    self.assertFalse(availability.invoice_grade_cost)
    self.assertFalse(availability.total_compute)
    self.assertIn("selector_usage_unavailable", availability.reasons)
```

- [ ] **Step 2: Run focused tests and verify RED**

```powershell
python -m unittest tests.test_iclr2027_usage_ledger -v
```

- [ ] **Step 3: Implement exact usage-event categories**

Use `event_kind` in `{agent_inference, selector_inference, deterministic_control, retry_attempt}` and `attempt_status` in `{successful, failed, unavailable}`. Every event binds trajectory, turn/control index, provider/model, input/output/cached tokens, duration, and cost or a nonempty unavailable reason. Never translate missing events into zero usage.

- [ ] **Step 4: Materialize and receipt usage artifacts**

Agent events come from persisted turn usage. Retry events come from immutable error rows. Selector/control events are emitted as explicit `unavailable` coverage records when absent. Re-run Task 3's CLI and confirm `claim_availability.json` permits only visible-agent token claims.

### Task 5: Train CATS and trajectory-level conformal calibration

**Files:**
- Create: `AG/AG-Research/iclr2027/cats.py`
- Create: `AG/AG-Research/train_exp09_cats.py`
- Create: `AG/AG-Research/tests/test_iclr2027_cats.py`
- Output: `AG/AG-Research/results/exp09_cats/models/`

**Interfaces:**
- Consumes: runtime features, private labels, group assignments, feature manifest, and `StudyContract`.
- Produces: fitted primary/logistic/sensitivity artifacts, `finite_sample_quantile`, `trajectory_nonconformity`, `CATSStopPolicy`, and hash-bound model manifests.

- [ ] **Step 1: Write exact conformal and hard-guard RED tests**

```python
def test_finite_sample_quantile_uses_corrected_rank():
    self.assertEqual(finite_sample_quantile(np.array([0.1, 0.2, 0.4]), alpha=0.25), 0.4)
    self.assertEqual(finite_sample_quantile(np.array([0.1, 0.2]), alpha=0.10), math.inf)

def test_trajectory_score_is_maximum_over_positive_prefixes():
    rows = pd.DataFrame({"beneficial_future": [0, 1, 1], "p_improve": [0.2, 0.8, 0.4]})
    self.assertEqual(trajectory_nonconformity(rows), 0.6)

def test_patience_and_hard_guard_both_required():
    policy = CATSStopPolicy(model=self.always_no_gain, q_alpha=0.2, patience=2)
    self.assertFalse(policy.observe(self.safe_prefix).stop)
    self.assertTrue(policy.observe(self.safe_prefix).stop)
    policy.reset()
    self.assertFalse(policy.observe(self.unsafe_prefix).stop)
    self.assertFalse(policy.observe(self.unsafe_prefix).stop)
```

- [ ] **Step 2: Run the focused test and verify RED**

```powershell
python -m unittest tests.test_iclr2027_cats -v
```

- [ ] **Step 3: Implement frozen preprocessing and classifiers**

Use `SimpleImputer(strategy="median", add_indicator=True)` and `StandardScaler()` for numeric columns plus `OneHotEncoder(handle_unknown="ignore", sparse_output=False)` for categoricals. Fit the complete `ColumnTransformer` on train sites only. Primary classifier is `HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=20260819)`. Sensitivity classifier is `LogisticRegression(max_iter=2000, class_weight="balanced", random_state=20260819)`.

- [ ] **Step 4: Implement trajectory-level calibration and fail-closed class checks**

Calibration uses one maximum nonconformity per calibration trajectory and the exact corrected rank from the spec. Reject one-class training labels, empty calibration trajectories, non-finite predictions, missing row IDs, or any group overlap; do not silently resplit or change epsilon/alpha.

- [ ] **Step 5: Train the frozen artifact matrix**

```powershell
python train_exp09_cats.py --dataset results/exp09_cats/dataset --output results/exp09_cats/models --all-frozen-variants
```

Generate primary HistGB at `(epsilon=.02, alpha=.10)`, logistic sensitivity at the same values, epsilon variants `.01/.05`, and alpha variants `.05/.20`. Each manifest binds feature order, train/calibration trajectory IDs, source receipt hashes, fitted transformer hash, model hash, scikit-learn version, parameters, epsilon, alpha, and quantile.

- [ ] **Step 6: Verify deterministic serialization by semantic manifest**

Train twice in isolated temporary output directories and assert identical predictions, parameters, feature order, source hashes, and calibration quantile. Do not require raw joblib bytes to match across platforms; bind each actual joblib byte hash in its own manifest.

### Task 6: Replay the exact eleven policies and evaluate the development gate

**Files:**
- Create: `AG/AG-Research/iclr2027/policy_replay.py`
- Create: `AG/AG-Research/replay_exp09_policies.py`
- Create: `AG/AG-Research/tests/test_iclr2027_policy_replay.py`
- Output: `AG/AG-Research/results/exp09_cats/replay/development/replay_rows.jsonl`
- Output: `AG/AG-Research/results/exp09_cats/replay/development/development_gate.json`

**Interfaces:**
- Consumes: immutable natural trajectories, separated dataset artifacts, usage ledger, and model manifests.
- Produces: exact `POLICY_REGISTRY`, `ReplayOutcome`, site-cluster bootstrap summaries, calibration coverage, and `ace.iclr2027.development_gate.v1`.

- [ ] **Step 1: Freeze baseline parameters in RED tests**

```python
EXPECTED_POLICIES = (
    "natural", "max_cap", "keyword", "lexical_du", "semantic_patience",
    "logistic", "uncalibrated_histgb", "state_conformal", "cats",
    "cats_no_guard", "oracle_peak",
)

def test_policy_registry_is_exact_and_ordered():
    self.assertEqual(tuple(POLICY_REGISTRY), EXPECTED_POLICIES)
```

Freeze `max_cap=3` agent turns; keyword signals from `PILOT_TERMINAL_SIGNALS`; lexical delta-utility `lambda_cost=0.1`, `epsilon=0.0`, `min_turns=2`, `patience=2`; semantic TF-IDF cosine similarity `>=0.85` for two consecutive comparisons; uncalibrated learned threshold `p_improve < 0.5` with patience 2; and oracle as the earliest maximum-quality prefix.

- [ ] **Step 2: Write exact prefix and outcome tests**

```python
def test_replay_never_synthesizes_or_reorders_messages():
    outcome = replay(self.trajectory, self.policy)
    self.assertEqual(outcome.message_hashes, self.trajectory.message_hashes[: outcome.stop_turn])
    self.assertEqual(outcome.visible_tokens, sum(self.trajectory.turn_tokens[: outcome.stop_turn]))

def test_only_oracle_receives_future_quality():
    for name, factory in POLICY_REGISTRY.items():
        if name != "oracle_peak":
            with self.assertRaises(TypeError):
                factory().observe(self.runtime_prefix, future_quality=[1.0])
```

- [ ] **Step 3: Run focused tests and verify RED**

```powershell
python -m unittest tests.test_iclr2027_policy_replay -v
```

- [ ] **Step 4: Implement replay outcomes and site-cluster statistics**

Persist trajectory/policy, stop turn, natural turns, stopped/full/oracle quality, visible-agent tokens and reduction, quality delta, hard-guard admissibility, unsafe/premature flags, overshoot, oracle regret, and exact prefix message hashes. Compute the mean quality-difference 95% CI with a deterministic 10,000-draw outer bootstrap over the two development-gate site groups; keep every case family, condition, topology, and repeat from a sampled site together.

- [ ] **Step 5: Evaluate the frozen development gate**

```powershell
python replay_exp09_policies.py --snapshot results/exp09_cats/development_snapshot/snapshot_receipt.json --dataset results/exp09_cats/dataset --models results/exp09_cats/models --partition development_gate --output results/exp09_cats/replay/development
```

CATS passes only when median visible-agent token reduction is at least 0.15, the site-bootstrap lower 95% bound for mean quality delta is greater than -0.03, observed unsafe stops equal zero, and empirical trajectory coverage is present. Persist every failed check; do not modify model, thresholds, assignments, or replay after seeing the gate.

- [ ] **Step 6: Verify all policy rows and receipts**

Require exactly `development_gate_trajectory_count * 11` unique rows, paired source identity for all policies, no missing/extra policy key, and byte/hash verification against model, dataset, usage, and snapshot receipts.

### Task 7: Emit a fail-closed method-lock candidate and update execution memory

**Files:**
- Create: `AG/AG-Research/iclr2027/method_lock.py`
- Create: `AG/AG-Research/freeze_iclr2027_method.py`
- Create: `AG/AG-Research/tests/test_iclr2027_method_lock.py`
- Modify: `AG/AG-Research/ICLR_2027_EXECUTION_MEMORY_2026-08-19.md`
- Output: `AG/AG-Research/results/exp09_cats/method_lock_candidate.json`

**Interfaces:**
- Consumes: design receipt, development snapshot receipt, failed pilot gate, dataset/usage/model/replay receipts, and development gate.
- Produces: a complete method-lock candidate with `held_out_access_allowed=false` and explicit blockers.

- [ ] **Step 1: Write a failing access-gate test**

```python
def test_negative_pilot_gate_cannot_emit_positive_method_lock():
    candidate = build_method_lock(self.complete_receipts, pilot_gate={"passed": False})
    self.assertFalse(candidate.held_out_access_allowed)
    self.assertIn("pilot_gate_failed", candidate.blockers)
    with self.assertRaises(PermissionError):
        require_positive_method_lock(candidate)
```

- [ ] **Step 2: Run the focused test and verify RED**

```powershell
python -m unittest tests.test_iclr2027_method_lock -v
```

- [ ] **Step 3: Implement the exact receipt closure**

Bind the approved design receipt, snapshot, runtime/private/assignment feature artifacts, fitted transforms, all frozen model variants and quantiles, exact 11-policy registry, replay implementation hash, usage schema and claim flags, bootstrap/statistical specification, pilot gate, and development gate. A missing or mismatched receipt fails closed.

- [ ] **Step 4: Freeze the real candidate without granting test access**

```powershell
python freeze_iclr2027_method.py --design-receipt ..\..\docs\superpowers\specs\2026-08-19-iclr2027-option-b-design.receipt.json --snapshot results/exp09_cats/development_snapshot/snapshot_receipt.json --pilot-gate results/exp08_architecture/pilot_full_v12_clean_recovery/pilot_gate.json --dataset results/exp09_cats/dataset/feature_manifest.json --models results/exp09_cats/models/model_registry.json --replay results/exp09_cats/replay/development/development_gate.json --output results/exp09_cats/method_lock_candidate.json
```

Expected: `held_out_access_allowed=false` with at least `pilot_gate_failed`; a negative CATS development gate adds `development_gate_failed`.

- [ ] **Step 5: Update the authoritative execution memory**

Record artifact paths and SHA-256 values, realized site/trajectory/label censuses, model/calibration results, all gate checks, claim-availability limits, and the exact blockers. State explicitly that no held-out artifact was opened and no additional LLM call occurred.

- [ ] **Step 6: Run full verification**

```powershell
python -m unittest discover -s tests -p "test_iclr2027*.py" -v
python -m compileall -q iclr2027 tests freeze_iclr2027_development.py build_exp09_dataset.py train_exp09_cats.py replay_exp09_policies.py freeze_iclr2027_method.py
python -m ruff check iclr2027 tests freeze_iclr2027_development.py build_exp09_dataset.py train_exp09_cats.py replay_exp09_policies.py freeze_iclr2027_method.py
git -C .. diff --check -- AG-Research
```

Expected: all tests pass and all three static checks exit 0. Do not proceed to held-out/OOD work; report the method-lock blockers to the user.
