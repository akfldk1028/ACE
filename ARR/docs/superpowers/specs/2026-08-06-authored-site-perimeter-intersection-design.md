# Authored five-edge site-perimeter intersection

## Goal

Create one new canonical `neighborhood_living` mass whose plan is a persisted direct-LLM abstraction of the generation host and south/SW access relation. The plan must not copy the legal upper-floor polygons and must not be generated at runtime.

## Approved design

One canonical UnitBox is scaled as the block BaseVolume and placed by the normalized `12.865:8.009` host aspect Matrix4. A separately authored five-edge `extruded_polygon` operand uses placed-local normalized points `[(0.18,0), (1.606318,0), (1.606318,1), (0,1), (0,0.18)]`. Intersecting it with the BaseVolume makes the southwest street facet.

The intersection receives one continuous z-axis architectural taper with `start_scale=[1,1]`, `end_scale=[0.90,0.86]`, and no section breakpoints. A terminal centered south notch uses `ratio=0.28`, `width_ratio=0.38`, and `height_ratio=0.58` to bind the active ground edge to street access.

The source body families are composition (`intersection`) plus deformation (`taper`), with one threshold (`notch`). The only canonical UnitBox count is one; the pentagon is a typed intersection operand. The bound path is the 1/1 long-axis extrude variation 1, `book:path:fda21c3dd4b1e6a2699ca4f80b6eecb223bd56e35a296e2358674d2b77d6a28e`, whose x-axis extrude is absent from source and does not expand z.

## Authorship and validation boundary

The host aspect and normalized access-side abstraction come from generation-site/program context. The five points, taper, and threshold values are direct architectural choices, not parcel coordinates, legal floor polygons, target-area vectors, or law-derived z controls. Freeze the persisted AST before canonical validation, validate exactly once, and do not change `.18`, `.90/.86`, or notch values after law feedback.

