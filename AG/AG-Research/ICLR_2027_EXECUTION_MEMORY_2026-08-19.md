# ICLR 2027 execution memory — 2026-08-19

This file is the authoritative checkpoint for the current architecture-domain run. It supplements the older domain memory without rewriting it.

## Scientific scope

- Main question: when should a multi-agent architecture review team `STOP_ACCEPT`, `STOP_REJECT`, or `CONTINUE` under hard evidence constraints?
- Current paper scope remains judge-free STOP/CONTINUE control. It is not a five-action routing/RL system.
- ARR supplies frozen architecture evidence; multi-agent topology changes only the review process.
- No model pilot, CATS fit, held-out test execution, or registry freeze has happened yet.

## Site protocol amendment

- Candidate source: 30 unique parcels, 25 initially eligible, 16 districts.
- Final held-out selection uses seed `20260818` and an explicit maximum parcel area of `30,000 m2`.
- The first five-site selection was invalidated before model execution because two parcels were far beyond the building-scale benchmark scope.
- The archived first selection is retained as `data/iclr2027/site_registry.v1_pre_area_cap.json` with SHA-256 `B0E127BE56ECEBF16B2C618995B5618E41C923BFC75F1B3A967CA025B090E6AB`.
- Final v2 test selection has five previously unobserved sites, five districts, no overlap with the archived selection, and parcel areas from 154.4 to 24,514.0 m2.
- Development expansion is outcome-blind: promote every archived v1 test site that satisfies the new <=30,000 m2 rule and all original availability predicates. This promotes all three qualifying sites and excludes the two oversized sites.
- Expected amended registry: five development sites and five final test sites; 15 native and 15 challenged cases per split.

## Final v2 ARR artifacts

All five sites were executed sequentially with the same three programs and diagnostic target 3. No site was replaced after observing outcomes.

| Anonymous site | Duration (s) | Summary bytes | Summary SHA-256 |
|---|---:|---:|---|
| test-v2-01 | 325.6 | 42,479,096 | `F709F9E617D7C4DA97275693ED38B69CACCEFDC196C436967DDE87FC6E73AADE` |
| test-v2-02 | 574.0 | 48,058,241 | `99ED05C15AB806943ACC94E4CBA78772A76CF1BF0BECAB3BC9CE5DC6CAFC86FB` |
| test-v2-03 | 347.3 | 31,997,895 | `78CC97642084E00F8C1348D02CBEE72DE793E2CDD04801BB5AA5D15F70E76AA7` |
| test-v2-04 | 2,137.8 | 9,046,084 | `E7581D9BBCC8C2B8F86F5384AD566E343A4D88974579DECE4CAA8B93A998A08F` |
| test-v2-05 | 279.3 | 16,577,201 | `5A5DD51265F89E81470DC3D8B7147E40BBC5CA1FE62753CFA43A880549B012E2` |

Site 4 exceeded the original 30-minute orchestration wrapper timeout, but the original Python process continued and completed all 36 candidates for the last program. It was not restarted; the completed summary above is the authoritative artifact.

## Held-out v2 decision census

Across 15 site-program cases, the independently validated native gold is:

- `STOP_ACCEPT`: 4 execution cases.
- `STOP_REJECT`: 10 cases.
  - preflight: 1
  - selection: 1
  - materialization / program routing empty: 7
  - materialization / all invocations failed: 1
- `CONTINUE`: 1 candidate-floor-context case with a missing typed candidate-level ledger.

No raw PNU is recorded in this checkpoint.

## Development challenge protocol

- The amended development native set has 7 execution subjects and 8 attempt-stage subjects.
- Seven execution subjects receive exactly one challenge each:
  - five hard-fault families: identity hash, law projection, parking shortage, program capacity, geometry compile;
  - two missing-evidence families: law evidence missing and parking evidence missing.
- Missing required evidence yields typed `CONTINUE`; present-but-failed evidence remains `STOP_REJECT`.
- Expected full development census after challenge integration: `STOP_ACCEPT=7`, `STOP_REJECT=21`, `CONTINUE=2` across 30 cases.
- Full pilot composition: 30 cases x 5 registered topologies x 3 repeats = 450 logical runs.
- A one-case smoke remains one case x one topology x one repeat and must use its own checkpoint directory.

## Leakage and integrity boundary

- Agent prompts already remove raw PNU, internal case ID, condition, and gold labels.
- Before freeze, bundles are being migrated to a typed `public/internal/gold` three-way format.
- Public IDs use a private HMAC-SHA256 projection namespace; raw PNU and internal case IDs remain only in the private registry/binding.
- Freeze must bind the canonical private registry projection, public projection, split manifest, all three bundle files, and their 1:1 hashes.
- Existing v1 bundles and unversioned Exp08 transactions must not resume into the v2 identity space.

## Current gate

Do not freeze or launch the 450-run model pilot until all of the following pass:

1. development amendment applied to the real registry;
2. all ten ARR summaries bound to the amended registry;
3. public/internal/gold v2 bundles built and independently verified;
4. registry freeze receipt validates after tamper tests;
5. final full ICLR test suite and compileall pass;
6. one-case paid-path smoke records actual duration, retries, visible tokens, selector usage, and cost-equivalent accounting.

## 2026-08-19 v9 pre-scale mini-pilot

The earlier v1-v8 runs are diagnostic-only because their parser, routing, prompt-transport, or runtime-identity contracts differ from the final protocol. The first protocol-valid five-topology run is `results/exp08_architecture/mini_six_five_v9`.

- Scope: six frozen development cases, five registered three-agent topologies, one repeat, 30 logical runs. This is a pre-scale mini-pilot, not the preregistered 450-run development pilot.
- Completion: 30/30 completed, zero terminal errors. One run retried after an incomplete final structured state and then completed; run-level retry rate 3.33%.
- Collaboration protocol: 30/30 runs contain geometry, compliance, and reviewer substantive turns; 30/30 end on the reviewer; zero empty agent turns; zero protocol violations.
- Final outcomes: parse 30/30, decision 30/30, admissibility verdict 30/30, blocking-issue match 30/30, and missing-evidence match 30/30. Gold and observed censuses both equal 5 `STOP_ACCEPT`, 20 `STOP_REJECT`, and 5 `CONTINUE` across topology repetitions.
- All-turn parse completeness: 115/118 = 97.46%. The three incomplete intermediate turns remain visible and are not carried forward or hidden.
- Privacy audit: zero raw 19-digit parcel identifiers, known private case identifiers, projection secret values, forbidden condition/gold fields, or credential markers in the run manifest, plan, summary, and transactions.
- Runtime: actual invocation wall time 3,122.2 seconds (52.0 minutes). Final successful-attempt durations sum to 3,003.4 seconds; the difference includes retry and orchestration overhead. The topology totals were rr3 577.9 s, sel3 735.1 s, swm3 467.4 s, refl3 438.7 s, and debate3 784.4 s.
- Visible agent-turn token accounting: 333,067 total (137,917 input and 195,150 output). Selector/control calls may be absent, so this is not invoice-grade accounting.
- Resume check: repeating the exact command completed in 3.5 seconds with zero new completions and all 30 runs skipped.
- The resume check exposed and then closed a provenance bug: an all-skip invocation had overwritten the original execution counters in the executed manifest. The runner now preserves an existing executed manifest byte-for-byte on an exact no-op resume and fails closed on any non-noop delta. A partial resume also derives final execution counts from the strict full transaction summary rather than the latest invocation delta; clean and terminal-error cases are both tested. The v9 manifest was restored from the original invocation output and immutable transaction/summary counts, then revalidated as 30 completed, zero skipped, zero errors, 118 parsed turns, and 115 successfully parsed turns.
- Integrity verification: all 30 transactions passed strict identity/schema validation and semantic recomputation; frozen source audit verified all four bundles; the focused ICLR suite passed 235/235 tests; Ruff, compileall, and `git diff --check` passed.

Pre-scale ruling: the v9 mini-pilot passes the protocol and task-quality expansion gate. Do not describe it as the full development result or as evidence of topology superiority: each topology saw only six cases and all five achieved identical final correctness. A naive serial scale-up is about 13 hours, but it is only a planning proxy and excludes variance, additional retries, and unmetered selector/control usage. The full 30-case x five-topology x three-repeat = 450-run pilot remains unexecuted and requires an explicit large-run authorization. Final verification after the complete provenance fix passed 239/239 ICLR tests; independent review reports Critical 0 and Important 0.

## 2026-08-19 full development pilot start

- The user explicitly authorized the 450-run development pilot after the v9 pre-scale gate.
- Authoritative checkpoint: `results/exp08_architecture/pilot_full_v10`.
- Frozen plan: 30 development cases x five registered topologies x three repeats = 450 logical runs; development decision census is 7 `STOP_ACCEPT`, 21 `STOP_REJECT`, and 2 `CONTINUE` before topology/repeat expansion.
- A fresh dependency-bound dry run validated the v2 manifest, 450 unique resume identities, six neutral frozen input hashes, full plan hash, stage census, decision census, and privacy boundary. Independent preflight review reported Critical 0 and Important 0.
- Actual execution started with the Claude Haiku model through the existing Claude subscription transport. Early checkpoint at two transactions: 2 completed, zero terminal errors, zero retried runs. This is operational status only, not a scientific result.
- Initial one-sample projection suggested approximately 14.5 serial hours and 6.47M visible tokens, but this is not a reliable ETA or invoice-grade accounting. Re-estimate after multiple completed transactions.
- Independent paper-readiness ruling: current ICLR readiness is LOW; a clean 450-run development pilot raises it to MEDIUM, not HIGH. Accept-level evidence still requires the calibrated stopping method, strong baselines, frozen held-out primary testing, OOD/cross-model evidence, site-aware statistics, and bounded expert validation for architectural validity claims.

## 2026-08-19 v10 interruption and provenance-clean replacement

- `pilot_full_v10` was stopped after an interrupted parent output channel made diagnostic `stderr` writes raise `OSError: [Errno 22] Invalid argument`. The transport wrapper incorrectly allowed this diagnostic failure to invalidate successful SDK/subprocess calls.
- Frozen v10 incident boundary: 289 strict JSON transactions, 56 completed, 233 terminal errors, and 699 failed attempts. All v10 outputs are diagnostic-only and are excluded from the development scientific snapshot.
- The fix was developed through explicit red/green tests covering SDK success, SDK failure, SDK fallback, subprocess success, import diagnostics, and over-limit prompt diagnostics. Fresh verification passed 244/244 ICLR tests, compileall, Ruff, and `git diff --check`.
- Isolated recovery smoke `smoke_stderr_recovery_v11` completed 1/1 with zero errors/retries and 9/9 parsed prefixes. The original 56 completed transaction commitment remained `f27350ccdb4b468b30ee9421586fac574186814d9375ed9f3ca70f320a1118fb` before and after smoke.
- In-place v10 resume was rejected because the verified repair changes the code identity. Old identity: `179fe49607a33e2eca5337bb099cde78be96055b-dirty-6278f0bc2a6b4085-deps-1b80c990bb34d4a1`. Replacement identity: `179fe49607a33e2eca5337bb099cde78be96055b-dirty-89d4ae988d18b5c7-deps-48d730d98a916537`.
- Option B was frozen as an approved prospective amendment, explicitly disclosed as occurring after development collection started but before CATS training/calibration, method lock, or test access. Design receipt SHA-256: `95f54cbd8ec5ea0700d967b9128d568690fcb118eda588dff35917e007f532a1`.
- Provenance-clean replacement `pilot_full_v12_clean_recovery` started in a hidden background Python process, PID `97444`, with durable stdout/stderr logs outside the transaction directory.
- Replacement plan: 450/450 unique resume identities; identical frozen input, registry, identity, and split commitments; stage census 14 execution, 6 materialization, 4 preflight, 6 selection; decision census 7 `STOP_ACCEPT`, 21 `STOP_REJECT`, 2 `CONTINUE`; run-plan SHA-256 `7672205a2cdbf8f5b5c929744e58d31c086e7765cb166a80a9a17f59f458b7c9`.
- First replacement transaction `e9e4314bded610de0c958085828250e8e79609d76641a920b6f511355243b9f1.json` passed strict validation: completed, zero error/retry rows, 9/9 prefixes parsed, 16,634 visible tokens, 228.64 seconds, and no incident signature. Transaction SHA-256: `38bc1fd29548e38772fe1c57b1c215026773903d66ee50bc47dc8e017be29716`.
- Do not modify Python/runtime dependency files while v12 is running. Do not train CATS or access held-out data until the clean 450-transaction snapshot and later method-lock gates pass.

## 2026-08-19 v12 operating-system reboot and in-place resume

- Windows Event Log records a restart initiated at `2026-08-19T11:53:03+09:00`; the event log stopped at 11:53:37 and the new boot started at 11:54:19.
- The last pre-restart completed v12 transaction was written at 11:50:07. The first terminal error was written at 11:53:08, after restart initiation. The common transport exit code was decimal `3221226091` / NTSTATUS `0xC000026B` (`STATUS_DLL_INIT_FAILED_LOGOFF`).
- Frozen interruption boundary: 93 strict-valid transactions, comprising 49 completed and 44 terminal-error transactions; 357 of 450 identities were unattempted. The 49 completed filename/hash mapping commitment was `c213a0b94c1b5f17e99c0d5e60a65cc86b64ea882668eeb881f3a41ba447f098`.
- The frozen run plan remained 450 unique identities with SHA-256 `7672205a2cdbf8f5b5c929744e58d31c086e7765cb166a80a9a17f59f458b7c9`. The current code/runtime identity still exactly matched the v12 manifest: `179fe49607a33e2eca5337bb099cde78be96055b-dirty-89d4ae988d18b5c7-deps-48d730d98a916537`.
- Focused pre-resume verification passed 31/31 tests. The user explicitly authorized continuing from the existing checkpoint rather than restarting the full pilot.
- In-place resume started at `2026-08-19T12:09:00+09:00` as hidden Python PID `9564`. New durable logs are `pilot_full_v12_clean_recovery.resume_20260819_120900.stdout.log` and `.stderr.log`; the original logs were not overwritten.
- The first retried identity `032859982f90db1db05c38f92486fe87938113b50ca29c3a5ce16b0c1dc358bb` completed successfully with all three parsed prefixes complete, 13,677 visible tokens, and 153.17 seconds. Its three pre-restart error rows remain in the transaction lineage. The original 49 completed mapping commitment remained unchanged after this retry.
- By `2026-08-19T13:06+09:00`, all 44 reboot-induced terminal-error identities had been retried successfully with their prior three-attempt error lineage retained. Strict validation then showed 95 completed transactions, zero terminal-error transactions, all 90 `rr3` runs complete, and 5 `sel3` runs complete. The original 49 completed mapping commitment remained unchanged.
- Continue polling transaction state and process liveness. Stop on a repeated common terminal-error signature, completed-artifact mutation, code-identity drift, or run-plan drift. Do not access held-out data or fit CATS before the 450-transaction development snapshot gate.

## 2026-08-19 v12 second reboot, completion, and independent gate

- A second Windows boot began at `2026-08-19T18:25:50+09:00`. The preceding v12 stderr log stopped at 18:25:07 and the last completed transaction was written at 18:23:07, so the stopped Python process was attributed to the operating-system reboot rather than a persisted terminal transaction error.
- The post-reboot boundary contained 419 strict-valid transactions, all completed: `rr3=90`, `sel3=90`, `swm3=90`, `refl3=90`, and `debate3=59`. The original 49-file commitment still equaled `c213a0b94c1b5f17e99c0d5e60a65cc86b64ea882668eeb881f3a41ba447f098`.
- Fresh pre-resume verification passed 31/31 focused transport, runner, and transaction tests. The computed code/runtime identity exactly matched the frozen v12 identity `179fe49607a33e2eca5337bb099cde78be96055b-dirty-89d4ae988d18b5c7-deps-48d730d98a916537`, and the run-plan SHA-256 remained `7672205a2cdbf8f5b5c929744e58d31c086e7765cb166a80a9a17f59f458b7c9`.
- In-place resume started at `2026-08-19T19:58:53+09:00` as hidden Python PID `47720`, using new durable logs `pilot_full_v12_clean_recovery.resume_20260819_195853.stdout.log` and `.stderr.log`. It skipped 419 completed identities and completed the remaining 31.
- The provenance-clean development snapshot finished at 450/450 completed transactions with zero terminal errors, 1,524 parsed prefix rows, 1,481 parse-complete prefix rows, and 450/450 parse-complete final states. The transaction-set SHA-256 is `3e7e9c0edd5fc8b1f2cc77f69da6dca9e381018d117a2cf3e8e6a4e94459de74`.
- Exact no-op replay completed in 5.8 seconds with zero new completions and all 450 identities skipped, revalidating the complete transaction set without model calls.
- The independent legacy pilot gate is negative and remains visible. Passed integrity checks include complete composition, exact manifest/schema, transaction binding, final parse completeness, protocol validity, decision census, zero terminal errors, and deadline/cost recording. Failed performance checks are final decision accuracy `427/450 = 0.948888...` (<0.95), final blocking accuracy `413/450 = 0.917777...` (<0.95), final verdict accuracy `408/450 = 0.906666...` (<0.95), and retried-run rate `50/450 = 0.111111...` (not <0.05). Final missing-evidence accuracy is `449/450 = 0.997777...`.
- Fresh repository verification after completion passed 244/244 ICLR tests, `compileall`, Ruff, and `git diff --check`.
- Do not alter the failed gate, thresholds, or collected transactions. Do not access held-out/test artifacts. The next permitted work is development-only: bind a formal development snapshot receipt, physically separate prefix-only runtime features from private labels, freeze site-group assignments before feature fitting, train/calibrate CATS, and run offline development replay. Held-out/OOD execution remains blocked until a positive method-lock receipt.

## 2026-08-20 Task 1-7 development continuation and method-lock denial

This append-only continuation supersedes the earlier pre-CATS status statements without rewriting them.

### Frozen scientific identity

- Transaction set SHA-256: `3e7e9c0edd5fc8b1f2cc77f69da6dca9e381018d117a2cf3e8e6a4e94459de74`.
- Run-plan SHA-256: `7672205a2cdbf8f5b5c929744e58d31c086e7765cb166a80a9a17f59f458b7c9`.
- Code/runtime identity: `179fe49607a33e2eca5337bb099cde78be96055b-dirty-89d4ae988d18b5c7-deps-48d730d98a916537`.

### Task 1-6 receipt and artifact closure

- `results/exp09_cats/dataset/feature_manifest.json` SHA-256 `7afe02f50c7b179c659b19042413d45d6940fa68444831359177e422262136a1`.
- `../../docs/superpowers/specs/2026-08-19-iclr2027-option-b-design.md` SHA-256 `95f54cbd8ec5ea0700d967b9128d568690fcb118eda588dff35917e007f532a1`.
- `../../docs/superpowers/specs/2026-08-19-iclr2027-option-b-design.receipt.json` SHA-256 `c86ce17e923d3a6988ed93d14c55f0ef7271b3a88eb94a44b88bf686ceee9da5`.
- `results/exp09_cats/replay/development/development_gate.json` SHA-256 `e4f64639991b617955b4e2f2821a46205e0d7dd5f9b79aef4fd883b729c565b5`.
- `results/exp09_cats/models/model_registry.json` SHA-256 `c30e5abd4b82ac652ae684376251b8b0bd836f28ebe84e8c815180f16ab702d8`.
- `results/exp08_architecture/pilot_full_v12_clean_recovery/pilot_gate.json` SHA-256 `d534eeb379e4fbe8793ff986fa2e583eca7b6783d561f968a606be0139b945a6`.
- `results/exp09_cats/development_snapshot/snapshot_receipt.json` SHA-256 `63556ffe60f0cfbbc7f5bea4f2d75e4bbafa67566a3bd9a8f61d22ad298b5a4d`.
- `dataset/feature_manifest.json` SHA-256 `7afe02f50c7b179c659b19042413d45d6940fa68444831359177e422262136a1`.
- `dataset/private/group_assignments.json` SHA-256 `77b7caf3369f429ff9aefb7636192cfd3476f3ab8b5cd873b230e9904d2b52c4`.
- `dataset/private/private_labels.jsonl` SHA-256 `3adc2b1afe484926d1825d34211bf86b5089af742868d0935c45ba3e7503a967`.
- `dataset/runtime/runtime_features.jsonl` SHA-256 `b7876d535316e31bdb00a5c514fba6ab0fa1ea5c8029dd6c62ed8e5d6f91d45f`.
- `dataset/usage/claim_availability.json` SHA-256 `8bb7844c2a6f3f6c83944698f94d9933d151e07ca959a4c7202d63d7a6db1286`.
- `dataset/usage/usage_events.jsonl` SHA-256 `01854249bac9c5d476e351f45035013c0a090dd783e5f4047c92f824dbf1f048`.
- `development_snapshot/snapshot_receipt.json` SHA-256 `63556ffe60f0cfbbc7f5bea4f2d75e4bbafa67566a3bd9a8f61d22ad298b5a4d`.
- `development_snapshot/source_artifact_sha256` SHA-256 `871a12b0f5785d229ccbd2ce3f283f8d47d6b8c37671645589f484273790cf92`.
- `development_snapshot/source_file_set_sha256` SHA-256 `75f9098dcc98c120f65e280e01a3055cbe9aa1bcb962f198908cfa507ff0ccf7`.
- `models/cats-alpha-0p05/classifier.joblib` SHA-256 `7404b2f0b0571bfecd80801aee276a51f7bd4c242ddbf78a4abba6202bb834d1`.
- `models/cats-alpha-0p05/manifest.json` SHA-256 `2d3ea060f090444b674d4df56e0120fd37d8074b9ad8b0b9949879736bd03bac`.
- `models/cats-alpha-0p05/predictions.jsonl` SHA-256 `fdd453935bbc29fd4f8a3043bb84e5f185ad03c2783e856fc9d80b21fa9315bb`.
- `models/cats-alpha-0p05/transformer.joblib` SHA-256 `69cfb8b4882faa6c5c967f1f2c9476d08cf69c2c86b0a627cc9a375da13ea956`.
- `models/cats-alpha-0p20/classifier.joblib` SHA-256 `7404b2f0b0571bfecd80801aee276a51f7bd4c242ddbf78a4abba6202bb834d1`.
- `models/cats-alpha-0p20/manifest.json` SHA-256 `3d51238a3c8d0f7fb7c35f7866cd9aae83ba52c3628f06d2ac3ef69b72e12cdc`.
- `models/cats-alpha-0p20/predictions.jsonl` SHA-256 `fdd453935bbc29fd4f8a3043bb84e5f185ad03c2783e856fc9d80b21fa9315bb`.
- `models/cats-alpha-0p20/transformer.joblib` SHA-256 `69cfb8b4882faa6c5c967f1f2c9476d08cf69c2c86b0a627cc9a375da13ea956`.
- `models/cats-epsilon-0p01/classifier.joblib` SHA-256 `7404b2f0b0571bfecd80801aee276a51f7bd4c242ddbf78a4abba6202bb834d1`.
- `models/cats-epsilon-0p01/manifest.json` SHA-256 `29061f6291ef1bbca71004ff94ec3ca699650cd50ea141475ddf3213a177aea7`.
- `models/cats-epsilon-0p01/predictions.jsonl` SHA-256 `fdd453935bbc29fd4f8a3043bb84e5f185ad03c2783e856fc9d80b21fa9315bb`.
- `models/cats-epsilon-0p01/transformer.joblib` SHA-256 `69cfb8b4882faa6c5c967f1f2c9476d08cf69c2c86b0a627cc9a375da13ea956`.
- `models/cats-epsilon-0p05/classifier.joblib` SHA-256 `7404b2f0b0571bfecd80801aee276a51f7bd4c242ddbf78a4abba6202bb834d1`.
- `models/cats-epsilon-0p05/manifest.json` SHA-256 `24ba2c5763fdd0d411e1a080cb9944c01e1f70091411789fbfe7936c1ef411f3`.
- `models/cats-epsilon-0p05/predictions.jsonl` SHA-256 `fdd453935bbc29fd4f8a3043bb84e5f185ad03c2783e856fc9d80b21fa9315bb`.
- `models/cats-epsilon-0p05/transformer.joblib` SHA-256 `69cfb8b4882faa6c5c967f1f2c9476d08cf69c2c86b0a627cc9a375da13ea956`.
- `models/cats-logistic/classifier.joblib` SHA-256 `e9c6d6ddd30738fb965a51eb94ffc1bd859dca7ccf6b0eaae03261cda562de45`.
- `models/cats-logistic/manifest.json` SHA-256 `e98432c0f31e3e2e8c2849094b4937c668a028495cb6290153ea21d405056934`.
- `models/cats-logistic/predictions.jsonl` SHA-256 `1b61f813b98a2f17ae47214af5a2274c344f44d4102cada72b2d09654edaee8f`.
- `models/cats-logistic/transformer.joblib` SHA-256 `69cfb8b4882faa6c5c967f1f2c9476d08cf69c2c86b0a627cc9a375da13ea956`.
- `models/cats-primary/classifier.joblib` SHA-256 `7404b2f0b0571bfecd80801aee276a51f7bd4c242ddbf78a4abba6202bb834d1`.
- `models/cats-primary/manifest.json` SHA-256 `236b4e3bc62a082947a82c476d0a579281f6f9b5c5b4b7bbe707f0c68685c0bc`.
- `models/cats-primary/predictions.jsonl` SHA-256 `fdd453935bbc29fd4f8a3043bb84e5f185ad03c2783e856fc9d80b21fa9315bb`.
- `models/cats-primary/transformer.joblib` SHA-256 `69cfb8b4882faa6c5c967f1f2c9476d08cf69c2c86b0a627cc9a375da13ea956`.
- `models/model_registry.json` SHA-256 `c30e5abd4b82ac652ae684376251b8b0bd836f28ebe84e8c815180f16ab702d8`.
- `models/registry.json` SHA-256 `c30e5abd4b82ac652ae684376251b8b0bd836f28ebe84e8c815180f16ab702d8`.
- `models/semantic_determinism.json` SHA-256 `2584b1438e20e60571f38042ef3ac7f291dff47f52406c354db97a3a0a30658f`.

### Development censuses and fitted artifacts

- Site split: `{"calibration":1,"development_gate":2,"train":2}`; trajectory split: `{"calibration":90,"development_gate":180,"train":180}`; prefix split: `{"calibration":270,"development_gate":708,"train":546}`.
- Dataset row census: `{"assignments":450,"prefixes":1524,"private_labels":1524,"runtime_features":1524,"sites":5,"trajectories":450}`; vocabulary size `6142` with SHA-256 `a5482a9706575276c9b51653cc51516c0ab1ded2f3bc1b2b4aacc20e0788222d`.
- Usage event census: `{"agent_inference.successful":1524,"deterministic_control.unavailable":450,"retry_attempt.failed":138,"selector_inference.unavailable":450}`; usage-events SHA-256 `01854249bac9c5d476e351f45035013c0a090dd783e5f4047c92f824dbf1f048`.
- Model census: `6` variants and `24/24` bound scientific artifacts; semantic determinism `48/48` comparisons true.
- `cats-primary` family `histgb`, epsilon `0.02`, alpha `0.1`, q `0.07273602024526815`, semantic SHA-256 `db76793bf29641446ca071c0e0b94356916bb936a6b054fc1c2f4a318a3df701`.
- `cats-logistic` family `logistic`, epsilon `0.02`, alpha `0.1`, q `1.7131800098546535e-06`, semantic SHA-256 `fae382537459ad33bd5968496231601e352ad0670b4c18adad6422b6a5c8bd3b`.
- `cats-epsilon-0p01` family `histgb`, epsilon `0.01`, alpha `0.1`, q `0.07273602024526815`, semantic SHA-256 `dff7e0592e71de102f3ba44f90b979b02cf1a02088de5dbc71e7a8feded5ac59`.
- `cats-epsilon-0p05` family `histgb`, epsilon `0.05`, alpha `0.1`, q `0.07273602024526815`, semantic SHA-256 `21b840f2c8b2f0622aed0acf38662319c91476c10a125c3289d27aefe8d28eb0`.
- `cats-alpha-0p05` family `histgb`, epsilon `0.02`, alpha `0.05`, q `0.9409436904527743`, semantic SHA-256 `799b9f138ab555668dbf2c4771680379ef88a22b3aeff4911084faca513b3dec`.
- `cats-alpha-0p20` family `histgb`, epsilon `0.02`, alpha `0.2`, q `0.0`, semantic SHA-256 `2263f015431a8fa82f34b888475aa80af5f3f2653374c47aa6405ddcef093c54`.
- Replay census: `{"development_gate_sites":2,"policies":11,"replay_rows":1980,"trajectories":180}`; replay rows SHA-256 `3cb1a50a26b8839d3e2fefa713aee5dd64ce26df8ff9e5f0aef4f294c1645be1`.
- State-conformal calibration uses `calibration` rows, q `0.9954265077154284`, and `adapted_after_development_outcomes=false`.
- The legacy lexical comparator is algorithmically distinct, but its stop vector collides with max-cap on `180/180` trajectories; collision-vector SHA-256 `887abd475873159a12d30d86fc72aea9d70f5e0aefc45d3e683863bf4f0a1002`. No independent empirical contrast is claimed.

### Gates, usage boundary, and access decision

- Development check `cats_empirical_trajectory_coverage_present`: passed `true`, observed `0.9888888888888889`, operator `is_not_null`, threshold `None`.
- Development check `cats_mean_quality_delta_bootstrap_lower_gt_negative_0p03`: passed `true`, observed `-0.012222222222222223`, operator `>`, threshold `-0.03`.
- Development check `cats_median_visible_agent_token_reduction_gte_0p15`: passed `false`, observed `0.0`, operator `>=`, threshold `0.15`.
- Development check `cats_observed_unsafe_stops_eq_0`: passed `false`, observed `2`, operator `==`, threshold `0`.
- Development gate result: passed `false`; failed checks `["cats_median_visible_agent_token_reduction_gte_0p15","cats_observed_unsafe_stops_eq_0"]`.
- Pilot gate result: passed `false`; failed checks derived from false values `["final_blocking_at_least_95pct","final_decision_at_least_95pct","final_verdict_at_least_95pct","retry_rate_below_5pct"]`.
- Usage claim boundary: `Persisted non-user agent-turn input/output tokens only; excludes selector inference, deterministic control, failed retries, cached tokens, duration, and cost.` Visible-agent tokens are available, while invoice-grade cost is `false` and total-compute claims are `false` for reasons `["selector_usage_unavailable","deterministic_control_usage_unavailable","provider_usage_unavailable","cached_token_usage_unavailable","cost_usage_unavailable","duration_usage_unavailable","retry_usage_unavailable"]`. These limitations are not monetary or total-compute savings claims.
- Method-lock candidate `results/exp09_cats/method_lock_candidate.json` file SHA-256 `c4a16171c5328389185a1995ed1881bdf893a4afb788ac17cf405165918c7a8b`; canonical self-hash `f723b93785cb224a21f75a2716c78573d8f9866f91433f6ef7cfd39fe5c30743`; blockers `["development_gate_failed","pilot_gate_failed"]`.
- `held_out_access_allowed=false`.
- Access audit: zero restricted-bundle reads, zero additional LLM calls, zero model or transformer refits, and zero commits for Tasks 1-7.
- No held-out or OOD work may proceed. The failed pilot and development gates remain binding; no retuning or reinterpretation is authorized.
