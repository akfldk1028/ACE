# ARR Worker Agents Soul

This layer turns global agent infrastructure into reusable workers.

Workers should be inspectable as independent agent folders, but they can keep
their executable Python adapters in the existing `implementations/` package when
that is the stable runtime import path.
