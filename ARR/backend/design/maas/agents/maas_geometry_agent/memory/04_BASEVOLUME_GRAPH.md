# BaseVolume graph

Base form, affine pose, fraction scope, and orientation are independent axes.

1. `UnitBox` is the single normalized causal root.
2. An LLM-selectable typed base-form capability may be prismatic, elliptical,
   simplex/tetrahedral, profiled, curved, or another executable grammar form.
3. Exactly one authored global homogeneous `4x4 Matrix4` carries scale, pose,
   rotation and shear for the whole candidate.
4. BOOK p.3 then selects one exact fraction scope:
   `1/1, 3/8, 1/2, 1/4, 1/8, 1/16`.
5. Orientation is `long_axis`, `short_axis`, or `vertical`.
6. Ordered BOOK operations and typed CSG follow.

`1/1` means the full p.3 host scope; it does not mean “the only form is a
cube.” Ellipse/simplex are not fraction labels. A Matrix4 is not a shape recipe.
The cross-product of these axes supplies architectural diversity; no axis may
be silently dropped from the LLM offer.

