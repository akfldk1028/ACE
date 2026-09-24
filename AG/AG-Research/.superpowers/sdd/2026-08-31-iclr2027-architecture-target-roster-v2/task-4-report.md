# Task 4 report — dataset sidecar verification without legacy drift

Status: COMPLETE (commits: none).

## RED → GREEN

- RED command: `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterDatasetIntegrationTests -v`
- RED result: expected import failure: `verify_frozen_target_roster` was absent from `iclr2027.architecture_target_roster`.
- GREEN focused result: 2/2 passed after adding the standalone verifier and both-or-neither count helper.
- Required combined command: `C:\Python313\python.exe -E -B -m unittest tests.test_iclr2027_architecture_target_roster.TargetRosterDatasetIntegrationTests tests.test_iclr2027_dataset tests.test_iclr2027_freeze_v2 -v`
- Required combined result: 19/19 passed.
- Lint/result integrity: `ruff check` passed for the two production modules and target-roster test; `git diff --check` reported no whitespace errors for those paths.

## Legacy pre-change pins, rechecked after GREEN

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `data/iclr2027/site_registry.json` | 7,187 | `8DA7FD613C7E8F5E9CCBB2E5673446A1622F06795991DCD971370DD821B0FF91` |
| `data/iclr2027/split_manifest.json` | 976 | `3E4BE5FEBDA1DEDD4F4598CA5EF6B9D713757330C9563ABD357E9C13465DCCB6` |
| `data/iclr2027/site_registry.public.json` | 1,488 | `2BFBD42FDF82979B56966E80C26D803A6DC232EC39798DE236295F94863D9573` |
| `data/iclr2027/freeze_receipt.json` | 559 | `B2A942A4A100755E38B653B212059FD6E5C4237EA26ADB29DAB330D2E6DD128F` |
| `data/iclr2027/cases/dev.challenged.manifest.json` | 2,849 | `EAA3FCE318B3843C633052C64E35D3107E5F81B3AECD23779CBC993B30AE3082` |
| `data/iclr2027/cases/dev.native.manifest.json` | 2,833 | `1CABFE5EBC42FA32EB750781866AB40568AE7F41364BF9CC3FC022D0C18E5178` |
| `data/iclr2027/cases/test.challenged.manifest.json` | 2,853 | `8F3EC5E1ABE382EE7BAD136D802D17245BB96D383CBA2F7B88914312306A1B86` |
| `data/iclr2027/cases/test.native.manifest.json` | 2,837 | `984690F09F68A565FF9D65BFFB95F7E2B8254CA1B47DC649B4F8877438430E1E` |

All post-GREEN pins match their pre-change values exactly.

## Changed-file pins

| File | Bytes | SHA-256 |
|---|---:|---|
| `iclr2027/architecture_target_roster.py` | 40,429 | `2D873D179E537406273BA7BE18855A1EDD477FCA0B2A7BD58EBC5A7500ACC11D` |
| `iclr2027/dataset.py` | 31,859 | `B3469093D68E11B7F96266E1F2B5259E7AEE279AEDAFCB121E470E36FA31B99E` |
| `tests/test_iclr2027_architecture_target_roster.py` | 41,708 | `8D609EA6995DB88FAB4D94917A6506CB502523F9DFDDC372C7A75176463ADC45` |

## No-drift evidence

- `verified_development_target_count(None, None, ...)` returns `None`; supplying exactly one sidecar path raises the required `ValueError`.
- A verified temporary public sidecar returns `64` typed development targets, while the checked legacy registry remains unchanged: `PROGRAM_ORDER` remains the three-program tuple and its two development bundle counts remain 15 each (30 across native and challenged legacy bundles).
- No sidecar parameter was added to `build_native_cases`, `build_challenged_cases`, `build_cases`, `write_case_bundle`, or `registry_expected_bundle_counts`; no legacy data or bundle manifest was written.
- The verifier reads only regular, non-reparse files, requires exact canonical UTF-8/LF JSON objects, rejects duplicate JSON keys, and validates roster/receipt self-hashes, caller/roster/receipt projection commitment, roster-to-receipt hash binding, and recomputed public site/target-set hashes.
- Tests reject roster-content and roster-self-hash changes, receipt self-hash, wrong caller projection commitment, public-site-set and public-target-set hash mutations, either missing path, constructed symlink input, an extra trailing LF, and a trailing space before any count returns.

## Concerns

- This remains a standalone count sidecar. It does not materialize public cases or assert that the 34 target specifications have become 34 legacy case bundles.
- No development-manifest extension was added under the task ruling that limits Task 4 to the public verifier/helper and target-roster test; any later manifest binding must be separately specified alongside actual target artifacts.
