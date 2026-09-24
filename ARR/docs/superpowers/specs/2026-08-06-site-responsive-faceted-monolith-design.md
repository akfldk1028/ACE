# Site-responsive faceted neighborhood monolith

## Goal

Author one new direct Codex OAuth static AST for canonical `neighborhood_living`. It must read as a compact street-corner monolith rather than another stepped stack, remain within the source budget of two body-rule families plus one public threshold, and bind one compatible non-`extrude` BOOK path absent from the source program.

## Context and authorship boundary

The program dimensional context supplies a host long axis of `12.865 m` and short axis of `8.009 m`. Their ratio informs only the normalized BaseVolume placement Matrix4. No parcel coordinates, legal-floor polygons, target floor areas, or law-derived section heights enter the authored AST.

The plan facet, continuous recession plane, and terminal entry values are direct LLM architectural choices within the typed geometry contract. They are frozen before the canonical legal/capacity validation and will not be tuned after its outcome.

## Considered approaches

1. **Selected — southwest street facet plus continuous oblique recession.** A full `block` BaseVolume is placed at the host aspect ratio, receives one shallow southwest `cut_corner`, then one shallow oblique `slice`, followed by a centered south access-bound `notch`. This preserves capacity while giving plan and section different architectural work.
2. Southeast facet plus west entry. This is geometrically viable but the persisted diagnostic context does not identify a west access edge, so its street relation has weaker evidence.
3. Two plan facets plus entry. This would consume both body rules and omit the requested continuous upper recession.

## Frozen AST design

The graph is one unary lineage:

`UnitBox -> scale(block) -> Matrix4(host aspect) -> cut_corner(SW) -> slice(oblique upper recession) -> notch(south access threshold)`

- The Matrix4 is diagonal and contains the normalized host aspect ratio, not a legal placement.
- `cut_corner` is a shallow plan cut responding to the exposed street corner.
- `slice` uses one oblique half-space with `offset_ratio`; it contains no `z`, floor-index, or breakpoint parameter.
- `notch` is terminal, south-bound, and uses the minimum neighborhood threshold ratios so it remains legible without hollowing out the monolith.
- Body-rule families are `void` (`cut_corner`) and `cut` (`slice`): exactly two.
- The terminal public threshold count is exactly one (`notch`).
- BOOK path is unused 1/1 long-axis base-operative `rotate`, variation 0: `book:path:a09ad744acb3b85c7d71cf6ba4741d96e0ea09caafce5df56a3755d87552375f`.
- `rotate` is not pre-applied in the source graph.

## Verification and terminal decision

Package the single fragment, run v11 static authorship validation, and run the latest canonical `neighborhood_living` production preflight. Accept only if the exact result meets all gates, including capacity utilization `>= 0.70` and runtime `<= 120 s`. Otherwise archive the unchanged fragment with its exact rejection reason. Do not revise numeric values after validation.
