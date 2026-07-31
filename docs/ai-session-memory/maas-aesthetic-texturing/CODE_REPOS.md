# Cloned Code Repositories

All repositories below are cloned as external research references only. Do not
install their dependencies into the ARR backend virtualenv. Treat them as
read-only until an explicit adapter is designed.

Root:

```text
clone/maas-aesthetic-texturing/
```

## Repositories

| Folder | Repo | HEAD | Role |
| --- | --- | --- | --- |
| `UniTEX` | `https://github.com/YixunLiang/UniTEX.git` | `affa1e2` | long-term 3D texture backend candidate |
| `syn_arch_2025` | `https://github.com/itingtsai/syn_arch_2025.git` | `6cccb83` | architecture-specific 3D/facade synthesis reference |
| `MD-ProjTex` | `https://github.com/abyildirim/MD-ProjTex.git` | `15464b7` | multi-view projection texturing reference |
| `TEXTurePaper` | `https://github.com/TEXTurePaper/TEXTurePaper.git` | `81e539f` | baseline text-guided 3D shape texturing |
| `MVControl` | `https://github.com/WU-CVGL/MVControl.git` | `ad5ac2f` | multi-view control/depth/normal conditioning reference |
| `ConsistNet` | `https://github.com/JiayuYANG/ConsistNet.git` | `b7ed22a` | multi-view consistency reference |

## Integration Rule

- No direct imports from these repos in ARR runtime code.
- No dependency installation into `ARR/backend/.venv`.
- Build small adapters under `ARR/backend/design/maas/aesthetic/adapters/`
  only after input/output contracts are explicit.
- Prefer passing files through a separate worker process or GPU service.

## Current ARR Contract

ARR currently produces:

```text
*.multi-view.png
metadata.scene_graph = arr.maas.scene_graph.v0
```

Adapters should eventually consume:

```text
multi_view_sheet.png
scene_graph.json
camera_poses.json
depth/*.png
normal/*.png
silhouette/*.png
facade_planes.json
```
