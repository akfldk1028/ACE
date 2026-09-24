# Task 7 independent blocker review

## Verdict

FAIL / BLOCKED_VALIDATOR_CLOSURE.

Independent reproduction matched exactly:

- attempted mutations: 4,140
- accepted mutations: 5
- private canonical-set permutation invariants: 240
- exact-eight release invariant: 1
- omitted source object: raw `FileNotFoundError`

All five accepted cases survived fresh independent resealing and were not hash
collisions, shared-state contamination, or ordering artifacts.

## Findings

### Critical: target/site binding absent

Swapping one target between two sites while preserving 12/11/11 passes because
the target parser checks only membership and the roster checks only counts.
`TargetSpecV1` has no trusted site binding; locator comparison is only an
area-bin set. The first owner is the public roster parser. The pre-freeze
contract must define a site-scoped target-ref namespace or introduce a new
private commitment.

### Critical: evidence-family semantics collapse to a union

Swapping `geometry` and `law` source assignments and resealing spec/roster
passes. The target-spec parser checks five keys, nonempty sorted IDs, and a
self-hash, while admission flattens all families into one source set.
`SourceCaptureV1` contains no independent family declaration. The first owner
is admission verification with a private, receipt-bound source-family
classification.

### Important: public source-ID semantic leakage

`geometry`, `repeat-01`, and `alias-01` all pass in public `source_ids`.
The global protected regex omits these token families and the private identity
alias regex is not applied at the public source-ID parser. A dedicated opaque
public-source-ID grammar is required; broadening the global key regex would
reject legitimate schema keys.

### Important: missing source object escapes stable errors

`_is_reparse_point()` catches its first missing-file `lstat`, then
`_is_regular_file()` performs an unprotected second `lstat`. The exception
escapes before `source_capture_missing_or_changed`. The regular-file helper
must normalize this `OSError` path to `False`.

### Important: nested-order census gap

The 240 top-level private-set permutations are correct invariants (172 capture,
2 locator, 33 spec, 33 geometry). Existing production also rejects targeted
public/nested order witnesses. However the 4,140 matrix uses singleton nested
lists, so it does not enumerate these attacks. Add two-element order attacks
for every public target source list, every target-family list, and every
locator source list.

## Boundaries

No file was edited during review. No network/model/non-dry/git/protected-data
access occurred. Production and focused-test pins matched the Task 7 report.
