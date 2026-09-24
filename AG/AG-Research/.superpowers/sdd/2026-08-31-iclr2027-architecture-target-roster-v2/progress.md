# SDD ledger — plan: docs/superpowers/plans/2026-08-31-iclr2027-architecture-target-roster-v2.md

Started: 2026-08-31 Asia/Seoul
Spec: docs/superpowers/specs/2026-08-31-iclr2027-architecture-target-roster-v2-design.md
Plan SHA-256 at start: 626F2D05333EF94C5D8ACA1779F91202DD44A71337E7DAFB9AB7B469AC18D19D

Setup note: the prescribed WSL `sdd-workspace` command timed out during Git root resolution on the Windows-mounted repository. The same plan-scoped ignored workspace was created directly. No task implementation had started.

Ruling: Execute in the existing dirty shared master workspace — the user previously and repeatedly authorized continuing in this repository, while moving the extensive untracked research tree would create larger drift risk — if wrong, the cost is that this feature is not isolated in a branch and must be separated later.

Ruling: Do not create commits during tasks — the shared tree contains extensive user-owned untracked and modified work and the plan explicitly substitutes exact hashes/reports for commits — if wrong, the cost is a less convenient Git review range, mitigated by plan-scoped review packages built from explicit file snapshots.

## Preflight conflict/interface scan

| Rows | Producer / consumer check | Finding and ruling |
|---|---|---|
| Task 1 internal | Tests name `verify_target_roster`; implementation produces that exact name and record types. | Clean. |
| Task 2 internal | Admission tests consume Task-1 hashes and add source/locator/geometry/blind validators. | Clean. |
| Task 3 internal | Builder consumes Task-2 admission closure and emits Task-1/2 records. | Clean. |
| Task 4 internal | Dataset adapter consumes a verified receipt but must preserve legacy registry arithmetic. | Plan wording originally risked equating 64 targets with 64 bundle cases. Ruling: 64 is the combined typed-target count; legacy bundle count stays 30 until separately materialized. Plan corrected — if wrong, the cost is either invalid power counting or a larger case-materialization task. |
| Task 5 internal | New inventory view consumes receipt counts while existing authenticated authority remains absent. | Clean; no execution authorization is added. |
| Task 6 internal | Runner needs strict manifest keys and resume identity. | Existing manifest v2 is exact-keyed. Ruling: sidecar runs use exact v3; no-sidecar runs remain byte-compatible v2. Plan corrected — if wrong, downstream v2-only consumers will require explicit v3 adapters before any non-dry execution. |
| Task 7 internal | Mutation tests and real candidate admission consume all prior validators. | Clean; freeze is conditional and honest `NEEDS_CONTEXT` is an allowed result. |
| Tasks 1 → 2 | `architecture_target_roster.py` record and canonical hash APIs. | Names and types agree. |
| Tasks 1/2 → 3 | Exact record constructors and `verify_admission_inputs()`. | Names agree; builder may not self-issue blind or review receipts. |
| Tasks 1/3 → 4 | `verify_frozen_target_roster()` returns `FreezeReceiptV2`. | Plan defines the exact call and count semantics. |
| Tasks 1/3 → 5 | Receipt-derived immutable inventory view. | Counts are derived, never caller supplied. |
| Tasks 1/3/4 → 6 | Roster/receipt digests and projection commitment bind runner v3. | Initial unfrozen fixture example lacked identity; corrected to frozen registry inputs. |
| Tasks 1–6 → 7 | Final mutation and integration closure. | Focused commands cover every modified production surface, including `run_manifest.py`. |

Ruling: Candidate yields 12/11/11 are hypotheses, not evidence — no candidate is admitted unless distinct normalized target subjects prove the count without evidence-field, condition, alias, or repeat inflation — if wrong, the cost is failure to reach 8/64 rather than accepting pseudoreplication.

Ruling: The running five-site/30-unit subscription-CLI diagnostic remains a separate negative-oriented artifact and may continue, but none of its outcomes or hashes can select, alter, or enter this roster — if wrong, the cost is discarded compute rather than leakage into the design freeze.

Task 1: Ruling: The Task-1 interface accidentally listed private/blind/geometry/freeze records whose exact contracts belong to Tasks 2 and 3 — narrow Task 1 to `TargetRosterV1`, `canonical_sha256`, and `verify_target_roster`; Task 2 owns source/locator/blind/geometry and Task 3 owns `FreezeReceiptV2` — if wrong, the cost is a later interface adjustment, while inferring unspecified security contracts now would be worse.

Task 1: review failed — Critical: site/target/source row model contradicts the binding public schema; Critical: conditions/evidence families were admitted; Critical: mandatory protected categories were incomplete; Important: tests locked in the wrong schema.

Task 1: fix round 1/5 (4 addressed, 0 open; commits none; production 11D7E304600ADE22E0A5B9C192A2FA74CAFED989EDCF7ED7A4ECD7515FFA7B70; tests 527EEE6208D386E80CF5BD3CB454DE6C24F4F8DF6C205212D8668C82D835DCC8)

Task 1: complete (commits none, re-review clean)

Ruling: The approved design named target-spec and geometry checks but omitted their exact private record closures — add exact `architecture_target_spec.v1`, `architecture_geometry_receipt.v1`, and `architecture_blind_overlap_check.v1` fields before Task 2 — if wrong, the cost is a schema migration before real freeze; leaving them implicit would force security-critical inference now.

Task 2: review failed — Critical: non-dev split accepted; Critical: evidence-family aliases accepted as subject identity; Critical: Unicode-digit PNU accepted; Important: arbitrary private schema versions; Important: standalone false hard-pass accepted; Important: raw serialization TypeError escapes stable blockers; Important: insufficient admission tests.

Task 2: minor (deferred): frozen `TargetSpecV1` retains a mutable evidence-family mapping; final review must decide whether to make it deeply immutable.

Task 2: fix round 1/5 (7 addressed, 0 open; commits none; production 9D0B334F0C84689094B22296E7A1DCFC8F2E61178C581D16A0131987B61ABD26; tests B111FF2C1223395439B629CA761573D83F2F0D7AA9D4E8ACEE0C26043F7A18F6)

Task 2: complete (commits none, re-review clean; 1 deferred Minor)

Ruling: Task 3 previously left builder filenames, legacy 5/30 bindings, review authentication, and the full v2 receipt closure implicit — freeze them as exact schemas and exact input/output paths before dispatch — if wrong, the cost is a versioned builder/receipt migration; inferring them during implementation would weaken reproducibility.

Task 3: review failed — Important: publication lacks crash-durable directory flush; Important: final publication is not an explicit atomic no-replace primitive; Important: transaction-safety tests omit required race/layout/failure/census cases.

Task 3: minor (deferred): filesystem races/permission errors may escape as raw `OSError`; final review must decide stable-error normalization.

Task 3: fix round 1/5 (3 addressed, 0 open; commits none; builder 7E8E39E58083F60CC27603B708EBBEAC52DCFB4D6DF0C3D0CEF7F15B57D3F86B; production unchanged 7D08608C8AF8801CF79E679CE74E08807909DD5945E0850ED0299AC4B814DC18; tests 9E7C6A36CA2482EAF2E62D3F2FAF45F4E1B26FF46AC3DF803D1A7CEC21D95468)

Task 3: complete (commits none, re-review clean; 1 deferred Minor)

Ruling: Do not add sidecar arguments to legacy `build_cases`/bundle writers in Task 4 — the sidecar proves 64 typed targets but only 30 legacy cases are materialized, so binding it to those case entry points would imply false materialization — expose a standalone verified-count adapter until Task 7 has real target artifacts; if wrong, the cost is a small later API wiring change rather than scientific count drift.

Task 4: review pause — `dataset.py` changed after report from 31,859/B346...F99E to 32,652/57FD...4961. Read-only audit proved exactly 793 LF→CRLF insertions and zero source-content hunk; LF normalization recomputed the exact report pin.

Task 4: Ruling: restore the exact reviewed LF bytes with the installed `dos2unix` formatter and resume review — raw-byte identity is binding and mixed/CRLF source would invalidate the review package even though Python semantics are unchanged — if wrong, the cost is only a reversible newline normalization. Restored 31,859/B3469093D68E11B7F96266E1F2B5259E7AEE279AEDAFCB121E470E36FA31B99E; 19/19 focused tests pass.

Task 4: complete (commits none, review clean; production 2D873D179E537406273BA7BE18855A1EDD477FCA0B2A7BD58EBC5A7500ACC11D; dataset B3469093D68E11B7F96266E1F2B5259E7AEE279AEDAFCB121E470E36FA31B99E; tests 8D609EA6995DB88FAB4D94917A6506CB502523F9DFDDC372C7A75176463ADC45)

Task 5: review failed — Important: quoted undefined `Path` annotations are runtime-invalid and conflict with frozen no-I/O AST constraints; Important: tests do not independently pin receipt-to-view hashes/schema/self-hash/commitment.

Task 5: Ruling: use runtime-valid `Any` annotations for the two opaque path arguments rather than importing/defining `Path` inside the no-I/O pre-call authority module — the adapter only forwards values to the already secure public verifier and preserving the frozen pathlib/Path prohibition is more important than nominal path typing here — if wrong, the cost is reduced static precision on two arguments, recoverable later by moving the adapter to a dedicated I/O module.

Task 5: fix round 1/5 (2 addressed, 0 open; commits none; pre-call 9EA5DDEED9294E904F030F99B79A0162C5D96B6CE39F248FA3B4C1894579A714; tests 4F65C3A747993E8B45391DA9B3DE6C52633FDED4E3AE68E980F41FEC96C42757)

Task 5: complete (commits none, re-review clean)

Task 6: review failed — Important: `checkpoint_dir` was created before later
manifest validation, so a valid sidecar plus invalid model left an empty
checkpoint path.

Task 6: fix round 1/5 (1 addressed, 0 open; commits none; focused 9/9; exact
Task-6 36/36; broader target-roster/runner-v2 55/55; zero model calls)

Task 6: complete (commits none, re-review clean; run-manifest production
unchanged BB19ACA2C790910157DA50872C23282224CBE541BCEC997F798D4AAD154D0FA8)

Task 7: focused mutation RED found 4,140 attempted / 5 accepted plus one raw
filesystem exception; full gates stopped. Independent review confirmed two
Critical missing bindings (target-to-site and evidence-family semantics), two
Important root causes (public source-ID leakage and raw FileNotFoundError), and
one Important nested-order coverage gap.

Ruling: before any real release, refine the pre-freeze v1 contract with exact
`<site_ref>-target-NN` namespace binding and private source-capture
`evidence_families`; reject public semantic source-ID tokens and normalize
missing source objects to the stable error surface. This is chosen because the
current schema cannot distinguish cross-site/family reassignment from valid
input; if wrong, the cost is fixture/report repinning before any candidate
freeze, whereas leaving it unfixed permits pseudoreplication and evidence-role
drift.

Task 7: complete for validator closure after three fix rounds (4,524 attempted,
0 accepted; 240 set invariants; 1 release invariant; focused 51/51; combined
174/174; Ruff lint/format clean; independent review C0/I0/M0). Candidate
admission remains separate and no real release was frozen.

Task 7 candidate gate: NEEDS_CONTEXT / no freeze. Original and replacement
candidate sets lack an authoritative exact 12/11/11 census, complete reusable
target-level geometry, canonical PNU closure, and written rights clearance;
blind-overlap and independent admission receipts are also absent.
