# ICLR 2027 Pilot v10 Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recover the interrupted 450-run development pilot without changing its frozen run identities, losing retry lineage, or allowing diagnostic-output failures to invalidate successful model calls.

**Architecture:** Keep `pilot_full_v10` as the sole append-only transaction directory. Make diagnostic console output best-effort at the `AG_Cohub` transport boundary, prove the failure and fix with unit tests, validate the 56 completed transactions, then resume only incomplete/error identities with the exact frozen command. Treat the 233 terminal-error rows and 699 failed attempts as incident lineage; never count them as successful scientific observations.

**Tech Stack:** Python 3.13, `unittest`, AutoGen, Claude Agent SDK, PowerShell process supervision, SHA-256 artifact receipts.

**Spec:** `AG/AG-Research/ICLR_2027_ACCEPTANCE_DESIGN.md`; operational state is recorded in `AG/AG-Research/ICLR_2027_EXECUTION_MEMORY_2026-08-19.md`.

## Global Constraints

- Preserve all files already written under `results/exp08_architecture/pilot_full_v10/run_transactions/` until strict validation has completed.
- Preserve the frozen `run_plan.json` SHA-256 `856990f9ab39821fc0d4db31939e299d012c45d0f82d08db0f3f9d2cd2668f3f`.
- Do not read held-out/test bundles, fit CATS, or change prompts, topology definitions, split identities, thresholds, or quality weights during recovery.
- A diagnostic sink failure must never change a successful or failed model transport outcome.
- Resume only after the regression test, focused suite, transaction validation, and one-case smoke pass.
- Existing completed identities must be skipped byte-for-byte on resume; error identities may be retried while retaining prior error lineage.
- Do not claim invoice-grade cost savings until selector, control, agent, and retry usage are all metered.
- Do not commit or publish changes without explicit user authorization; use local verification checkpoints in this recovery session.

---

### Task 1: Freeze the incident boundary

**Files:**
- Create: `AG/AG-Research/ICLR_2027_PILOT_V10_INCIDENT_2026-08-19.md`
- Inspect: `AG/AG-Research/results/exp08_architecture/pilot_full_v10/run_plan.json`
- Inspect: `AG/AG-Research/results/exp08_architecture/pilot_full_v10/run_transactions/*.json`

**Interfaces:**
- Consumes: stopped process IDs, immutable transaction files, core artifact hashes.
- Produces: a human-readable incident receipt with exact counts, hashes, failure onset, and restart gate.

- [ ] **Step 1: Record the stopped-process evidence and frozen counts**

  Record 289 valid transactions, 56 completed runs, 233 terminal-error runs, 699 failed attempts, and zero invalid JSON files.

- [ ] **Step 2: Record the core artifact hashes**

  Record the SHA-256 values for `run_plan.json`, `run_manifest.json`, `checkpoint.jsonl`, and `errors_retries.jsonl` without modifying the result directory.

- [ ] **Step 3: Record the failure boundary**

  Record that the last completed transaction was written at `2026-08-19T10:05:04+09:00` and the first `OSError: [Errno 22] Invalid argument` transaction at `2026-08-19T10:06:46+09:00`.

- [ ] **Step 4: Validate every transaction with Python's JSON parser**

  Run a read-only parser over all `run_transactions/*.json`; expected: 289 valid, 0 invalid.

### Task 2: Make diagnostic output non-authoritative

**Files:**
- Modify: `AG/autogen_a2a_kit/AG_Cohub/sdk/client.py`
- Modify: `AG/autogen_a2a_kit/AG_Cohub/model_factory.py`
- Test: `AG/AG-Research/tests/test_iclr2027_model_factory_fallback.py`

**Interfaces:**
- Consumes: diagnostic text and the current `sys.stderr` stream.
- Produces: `_safe_stderr(message: str) -> None`, which never raises and does not replace the existing file log.

- [ ] **Step 1: Write the failing SDK-success regression test**

  Patch the SDK async iterator to return normally and patch `sys.stderr.write` to raise `OSError(22, "Invalid argument")`. Assert that `ClaudeSDK.query()` still returns `success=True`.

- [ ] **Step 2: Run the regression test and verify RED**

  Run: `python -m unittest tests.test_iclr2027_model_factory_fallback.ClaudeSubprocessFallbackTests.test_sdk_success_survives_broken_stderr -v`

  Expected: ERROR with `OSError: [Errno 22] Invalid argument` from `sdk/client.py`.

- [ ] **Step 3: Implement the minimal safe diagnostic helper**

  Add `_safe_stderr(message: str) -> None` in `sdk/client.py` with a single `try/except Exception` around `print(..., file=sys.stderr)`. Replace the SDK success and SDK failure prints with the helper.

- [ ] **Step 4: Route model-factory diagnostic prints through the helper**

  Import `_safe_stderr` alongside `_log_to_file`; use it for SDK fallback and subprocess completion diagnostics so either transport cannot be invalidated by a dead output handle.

- [ ] **Step 5: Run the regression test and verify GREEN**

  Run the exact test from Step 2; expected: PASS.

- [ ] **Step 6: Run the focused transport and Exp08 suites**

  Run: `python -m unittest tests.test_iclr2027_model_factory_fallback tests.test_iclr2027_runner_v2 tests.test_iclr2027_transaction_v1 -v`

  Expected: all tests pass with no traceback or warning.

### Task 3: Prove safe recovery before resume

**Files:**
- Inspect: `AG/AG-Research/results/exp08_architecture/pilot_full_v10/run_transactions/*.json`
- Create: a separate temporary smoke directory under `AG/AG-Research/results/exp08_architecture/`; never use `pilot_full_v10` for smoke traffic.
- Update: `AG/AG-Research/ICLR_2027_PILOT_V10_INCIDENT_2026-08-19.md`

**Interfaces:**
- Consumes: fixed transport, frozen run plan, existing completed transaction hashes.
- Produces: smoke evidence and an explicit PASS/FAIL resume decision.

- [ ] **Step 1: Hash all 56 completed transaction files**

  Store the sorted filename/SHA-256 mapping in the incident receipt before any resume.

- [ ] **Step 2: Run one isolated paid-path smoke case**

  Use the same model and one development case in a new checkpoint directory. Expected: completed transaction, no `OSError`, valid structured state, and actual token/duration accounting.

- [ ] **Step 3: Run strict transaction validation on the smoke directory**

  Expected: one completed identity, no invalid transaction, no privacy or protocol violation.

- [ ] **Step 4: Re-hash the 56 completed v10 transactions**

  Expected: exact equality with the pre-smoke filename/SHA-256 mapping.

- [ ] **Step 5: Resume the frozen pilot only if every preceding gate passes**

  Run the original command with the same split, five patterns, three repeats, model, checkpoint directory, paid-run confirmation, cost estimate, and completion date. The runner must skip the 56 completed identities and retry error/missing identities.

- [ ] **Step 6: Poll progress without attaching correctness to stdout/stderr**

  Read `checkpoint.jsonl`, `errors_retries.jsonl`, transaction counts, and process liveness at bounded intervals. Stop again if a new common terminal-error signature appears or completed transaction hashes change.

## Provenance amendment after Task 3

The diagnostic fix changes both the scoped dirty-code hash and runtime dependency hash. Consequently Step 5 may not resume `pilot_full_v10` under its old identity. The provenance-safe replacement is a clean 450-run namespace whose run plan is generated from the verified recovery identity. The 56 v10 completions and 233 v10 terminal errors remain immutable diagnostic evidence and are excluded from the replacement scientific snapshot.

### Task 4: Start a provenance-clean replacement pilot

**Files:**
- Create: `AG/AG-Research/results/exp08_architecture/pilot_full_v12_clean_recovery/`
- Update: `AG/AG-Research/ICLR_2027_EXECUTION_MEMORY_2026-08-19.md`

**Interfaces:**
- Consumes: verified recovery code identity, frozen private binding, same 30 public cases, same five patterns, same three repeats, same model.
- Produces: a new 450-identity run plan and append-only transaction directory with durable stdout/stderr logs.

- [ ] **Step 1: Verify the new checkpoint directory does not exist**

  Fail closed on any collision; do not delete or reuse a prior directory.

- [ ] **Step 2: Launch with durable redirected logs**

  Start a hidden background process with stdout and stderr redirected to files outside the transaction directory. Use the exact development matrix and verified current code identity.

- [ ] **Step 3: Verify the fresh run plan before accepting progress**

  Require 450 unique resume identities, the same case/stage/decision census, the same frozen input commitments, and the verified recovery code identity.

- [ ] **Step 4: Inspect the first completed transaction and first retry/error event**

  Continue only if the transaction is strict-valid and the incident `OSError` signature is absent. Stop immediately if a new common terminal failure appears.

- [ ] **Step 5: Monitor to the 450-transaction snapshot gate**

  Poll process liveness and immutable transactions. Do not fit CATS or read held-out data during collection.
