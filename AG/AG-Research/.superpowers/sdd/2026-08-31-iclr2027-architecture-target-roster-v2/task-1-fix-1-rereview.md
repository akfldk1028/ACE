# Task 1 Fix Round 1 re-review

1. Wrong site/source/target model — ADDRESSED at
   `iclr2027/architecture_target_roster.py:28-40`.
2. Legacy `evidence_families` / `conditions` acceptance — ADDRESSED at
   `iclr2027/architecture_target_roster.py:148-177` and tests lines 109-120.
3. Incomplete protected-channel audit — ADDRESSED at production lines 42-49,
   113-132 and tests lines 71-90, 122-126.
4. Noncompliant fixtures/tests — ADDRESSED at tests lines 28-68.

New breakage: none. Out of scope: later roster semantics and integration.

Verdict: PASS.
