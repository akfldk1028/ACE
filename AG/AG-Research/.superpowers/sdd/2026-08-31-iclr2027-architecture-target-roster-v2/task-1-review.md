# Task 1 review — initial

## Spec Compliance

FAIL.

- Site rows implement `{site_ref, site_sha256, sources}` instead of exactly
  `{site_ref, area_bin}`.
- Target rows implement `{target_ref, site_ref, target_spec_sha256,
  evidence_families, conditions}`; required `program`, `subject_kind`,
  `attempt_stage`, `route_kind`, and `source_ids` are absent.
- Public target `conditions` and evidence-family fields are accepted, directly
  violating the closed public contract and count-inflation constraint.
- Recursive protection omits required categories including PNU, URI/path,
  condition, outcome, mutation, and gold fields.
- Canonical root fields, fixed 3/34 counts, 12/11/11 allocation, dev split,
  byte-ordinal ordering, and self-hash checking are implemented.

## Task Quality

FAIL.

Critical:

- `iclr2027/architecture_target_roster.py`: `_SITE_KEYS`, `_SOURCE_KEYS`, and
  `_TARGET_KEYS` define the wrong public data model.
- `iclr2027/architecture_target_roster.py`: `_parse_target()` permits
  `evidence_families` and `conditions`.
- `iclr2027/architecture_target_roster.py`: `_PROTECTED_NAMES` /
  `_reject_protected()` omit mandatory protected categories.

Important:

- `tests/test_iclr2027_architecture_target_roster.py`: fixtures and assertions
  validate the noncompliant schema, so passing tests do not establish the
  required contract.

Minor: none.
