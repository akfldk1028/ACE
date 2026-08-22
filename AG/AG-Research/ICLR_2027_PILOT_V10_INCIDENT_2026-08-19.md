# ICLR 2027 development pilot v10 incident receipt

Status: stopped; recovery gate closed  
Incident date: 2026-08-19 (Asia/Seoul)  
Affected directory: `results/exp08_architecture/pilot_full_v10`

## Frozen boundary

The pilot Python process `107808` and its validated parent PowerShell process `100388` were stopped after repeated transport-diagnostic failures. Their command lines both named `run_exp08_architecture.py` and `pilot_full_v10`. No pilot process with that command remained after the stop.

Read-only validation after the stop produced:

- planned logical runs: 450;
- written transactions: 289;
- Python JSON-valid transactions: 289;
- invalid transaction JSON: 0;
- completed transactions: 56;
- terminal-error transactions: 233;
- recorded failed attempts: 699;
- distinct failed resume identities: 233;
- attempt census: 233 at attempt 1, 233 at attempt 2, and 233 at attempt 3.

The result directory must not be described as a completed development pilot or used as a 289-observation scientific sample.

## Core artifact receipts

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `run_plan.json` | 225722 | `856990f9ab39821fc0d4db31939e299d012c45d0f82d08db0f3f9d2cd2668f3f` |
| `run_manifest.json` | 1755 | `282f93a0a439dd0c47472dc1d23645e03c7c161e3a3b37a75e3b2a27fa9a71c4` |
| `checkpoint.jsonl` | 28835 | `c654f712215264a67032d25df02f42700ec81d300b90c66006e83e44f0f9e962` |
| `errors_retries.jsonl` | 748818 | `3e780243028664419d09fdf0710e6c9a077f009bc39f9622bf2f98e85139d313` |

These hashes describe the stopped incident boundary. `checkpoint.jsonl` and `errors_retries.jsonl` are derived ledgers and are expected to change after an authorized resume; `run_plan.json` must not change.

## Failure boundary and root-cause evidence

- Last completed transaction write: `2026-08-19T10:05:04.447600+09:00`.
- First terminal-error transaction write: `2026-08-19T10:06:46.948419+09:00`.
- Every terminal-error transaction has the headline `RuntimeError: OSError: [Errno 22] Invalid argument`.
- The final successful file diagnostic `SDK OK` entry occurred before the common failure regime.
- `AG_Cohub/sdk/client.py` prints an SDK-success diagnostic to `sys.stderr` before appending its fail-safe file diagnostic and returning `SDKResult(success=True)`.
- When that print raises, the broad SDK exception handler treats the diagnostic exception as an SDK failure; its failure diagnostic prints to the same broken stream and raises again.
- `AG_Cohub/model_factory.py` contains two additional authoritative `stderr` diagnostics on the SDK-fallback and subprocess-success paths.

Root-cause hypothesis accepted for TDD reproduction: the interrupted parent output channel left `sys.stderr` with an invalid Windows handle; diagnostic console output was incorrectly inside the transport outcome path. The regression test must reproduce the behavior with a stream whose write raises `OSError(22, "Invalid argument")` before production code changes.

## Recovery gate

Resume is forbidden until all conditions pass:

1. the broken-stderr regression test fails against the current implementation for the expected reason;
2. the minimal diagnostic isolation fix makes the regression test pass;
3. focused transport, runner, and transaction suites pass;
4. all 56 completed transaction hashes are captured and validate before and after smoke;
5. a one-case smoke in a separate checkpoint directory completes without the incident signature;
6. the exact frozen `run_plan.json` hash remains unchanged;
7. resume skips the 56 completed identities and retains all previous error lineage.

This receipt is operational provenance, not a preregistration and not a scientific result.

## Recovery verification and restart ruling

The transport isolation patch completed a test-first red/green cycle for SDK success, SDK failure, SDK-to-subprocess fallback, subprocess success, import diagnostics, and over-limit prompt diagnostics. Fresh verification after the final import cleanup produced:

- isolated smoke `smoke_stderr_recovery_v11`: 1 completed, 0 errors, 0 retries;
- smoke prefixes: 9 parsed, 9 complete;
- smoke duration: 206.58 seconds;
- smoke visible usage: 90 input, 15,198 output, 15,288 total tokens;
- original completed-transaction mapping commitment unchanged: `f27350ccdb4b468b30ee9421586fac574186814d9375ed9f3ca70f320a1118fb`;
- original frozen run-plan hash unchanged: `856990f9ab39821fc0d4db31939e299d012c45d0f82d08db0f3f9d2cd2668f3f`;
- full ICLR suite: 244 tests passed;
- compileall, Ruff, and `git diff --check`: passed.

An in-place v10 resume is rejected. The original code identity is `179fe49607a33e2eca5337bb099cde78be96055b-dirty-6278f0bc2a6b4085-deps-1b80c990bb34d4a1`; the verified recovery code identity is `179fe49607a33e2eca5337bb099cde78be96055b-dirty-89d4ae988d18b5c7-deps-48d730d98a916537`. Passing the original identity to modified code would falsify provenance. Therefore all v10 outputs remain diagnostic-only and the 450-run development snapshot must restart in a new namespace using the verified recovery identity.
