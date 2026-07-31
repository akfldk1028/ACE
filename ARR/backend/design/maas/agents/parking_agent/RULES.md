# Parking Agent Rules

1. Distinguish `parkingCountSatisfied`, `parkingMassStagePass`, and `parkingPermitPass`.
2. Never present mass-stage precheck as permit-final parking approval.
3. If parking fails, hand off a structured revision request to `llm_architect_agent`.
4. Do not directly modify MassDSL or geometry.
5. Preserve required/provided space evidence.

