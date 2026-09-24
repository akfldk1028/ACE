# Task 2 review — initial

Spec Compliance: FAIL. Task Quality: FAIL.

## Critical

1. Non-dev locators are admitted; `split` is only nonempty.
2. Evidence-family aliases such as `parking` are admitted as normalized
   subject identities.
3. Unicode `\d` permits non-ASCII 19-character PNUs.

## Important

1. Private record parsers accept arbitrary nonempty schema versions.
2. Standalone geometry-set validation accepts `hard_pass=false`.
3. Non-JSON-serializable malformed fields can escape as raw `TypeError`
   instead of stable `TargetRosterError` blockers.
4. Admission tests cover only three negative paths and omit a valid admission
   assertion and the remaining record/set/retention closures.

## Minor

- `TargetSpecV1.evidence_family_sources` is a mutable dictionary nested inside
  a frozen dataclass.

Full evidence and line references are preserved in the controller transcript.
