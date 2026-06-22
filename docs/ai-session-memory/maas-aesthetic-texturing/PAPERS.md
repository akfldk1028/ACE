# Paper Map

## Primary Direction

### 3D Synthesis for Architectural Design

- Venue: WACV 2025.
- Why it matters: architecture needs editable massing plus facade synthesis,
  not generic object-level text-to-3D.
- Fit for MAAS: keep legal MAAS geometry as the editable source of truth, then
  synthesize facade treatment.
- Source: https://openaccess.thecvf.com/content/WACV2025/html/Tsai_3D_Synthesis_for_Architectural_Design_WACV_2025_paper.html
- Local code: `clone/maas-aesthetic-texturing/syn_arch_2025`

### Multi-View Depth Consistent Image Generation

- Venue/source: CAADRIA 2025 / arXiv 2025.
- Why it matters: starts from architectural shoebox/massing representations and
  generates consistent multi-view architectural imagery.
- Fit for MAAS: MAAS can produce better-than-shoebox locked mass references,
  plus view/depth conditions.
- Source: https://arxiv.org/abs/2503.03068
- Local code: no confirmed official implementation in this session.

### UniTEX

- Venue/source: CVPR 2026 / arXiv 2025.
- Why it matters: lifts generated multi-view textures into a 3D texture function
  rather than relying only on fragile UV inpainting.
- Fit for MAAS: long-term texture backend candidate after MAAS can export mesh
  or view/depth packs.
- Source: https://arxiv.org/abs/2505.23253
- Local code: `clone/maas-aesthetic-texturing/UniTEX`

### MVPainter

- Source: arXiv 2025.
- Why it matters: frames 3D texture quality around three criteria ARR should
  also use: reference-texture alignment, geometry-texture consistency, and local
  texture quality.
- Method signal: multi-view diffusion with ControlNet-style geometric control,
  plus PBR attribute extraction/back-projection.
- Fit for MAAS: MAAS can already produce the geometry side of the condition
  pack. The missing part is normal/depth/facade-plane projection and a
  generated texture atlas, not a billboard render.
- Source: https://arxiv.org/html/2505.12635v1

### Make-A-Texture

- Venue/source: WACV 2025.
- Why it matters: emphasizes fast shape-aware texture generation using multiple
  viewpoints and depth-aware inpainting.
- Fit for MAAS: a practical target for the short loop: choose facade views,
  generate/complete textures, then apply them back to the mass surfaces.
- Source: https://openaccess.thecvf.com/content/WACV2025/papers/Gorelik_Make-A-Texture_Fast_Shape-Aware_3D_Texture_Generation_in_3_Seconds_WACV_2025_paper.pdf

### TexFusion

- Source: NVIDIA Toronto AI Lab.
- Why it matters: synthesizes textures for existing 3D geometry using
  text-guided image diffusion and view-consistent sampling.
- Fit for MAAS: confirms the core product direction: keep MAAS geometry fixed,
  synthesize texture from views, and preserve cross-view consistency.
- Source: https://research.nvidia.com/labs/toronto-ai/texfusion/

### MD-ProjTex

- Source: arXiv 2025.
- Why it matters: uses multi-diffusion projection to keep view textures
  consistent in UV space.
- Fit for MAAS: candidate for projection/texture consistency after MAAS exports
  facade/mesh surfaces.
- Source: https://arxiv.org/abs/2504.02762
- Local code: `clone/maas-aesthetic-texturing/MD-ProjTex`

### Pro-DG

- Source: arXiv 2025.
- Why it matters: combines procedural facade grammar with diffusion guidance.
- Fit for MAAS: closest conceptual match to the MAAS grammar/ontology approach
  for window rhythm and facade structure.
- Source: https://arxiv.org/abs/2504.01571
- Local code: no confirmed official implementation in this session.

## Supporting Direction

### TEXTure

- Why it matters: established text-guided texturing of 3D shapes through
  iterative view painting.
- Fit for MAAS: useful baseline for mesh texturing once MAAS exports clean mesh
  surfaces.
- Local code: `clone/maas-aesthetic-texturing/TEXTurePaper`

### MVControl

- Why it matters: multi-view ControlNet-style conditioning with depth/normal
  control signals.
- Fit for MAAS: useful reference for the exact controls MAAS should produce:
  depth, normal, edge, silhouette.
- Local code: `clone/maas-aesthetic-texturing/MVControl`

### ConsistNet

- Why it matters: multi-view consistency block for diffusion outputs.
- Fit for MAAS: useful reference for view consistency validation/generation.
- Local code: `clone/maas-aesthetic-texturing/ConsistNet`
