# MassDSL Agent Rules

1. Preserve `parameter_source`.
2. Preserve `rule_evidence`.
3. Reject missing sequence evidence as `needs_evidence`.
4. Do not hide rule-prior values as LLM-authored parameters.
5. Hand off only structured MassDSL proposals to `maas_geometry_agent`.

