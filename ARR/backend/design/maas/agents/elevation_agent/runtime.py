"""Generate hash-bound elevation evidence from one compiled MASS."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
from typing import Any
import uuid

from .contract import ElevationBundle
from .projection import render_mesh_views, triangle_normals

def generate_elevation_bundle(
    compilation: Any,
    output_root: str | Path,
    *,
    execution_id: str,
) -> dict[str, Any]:
    if str(getattr(compilation, "status", "")) != "compiled":
        raise ValueError("elevationAgent requires a compiled MASS")
    vertices = tuple(getattr(compilation, "vertices", ()) or ())
    triangles = tuple(getattr(compilation, "triangles", ()) or ())
    if not vertices or not triangles:
        raise ValueError("elevationAgent requires a non-empty indexed triangle mesh")
    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    views_directory = root / "views"
    views = render_mesh_views(
        vertices,
        triangles,
        views_directory,
        execution_id=execution_id,
    )
    bounds = getattr(compilation, "metrics", {}).get("bounds")
    if isinstance(bounds, list) and len(bounds) == 2:
        minimum, maximum = bounds
    else:
        minimum = [min(float(row[i]) for row in vertices) for i in range(3)]
        maximum = [max(float(row[i]) for row in vertices) for i in range(3)]
    program_hash = compilation.program.program_hash()
    geometry_hash = str(compilation.geometry_hash or "")
    condition_pack = {
        "schema_version": "arr.elevation_agent.condition_pack.v1",
        "identity": {
            "execution_id": execution_id,
            "program_hash": program_hash,
            "geometry_hash": geometry_hash,
        },
        "indexed_mesh": {
            "vertex_count": len(vertices),
            "triangle_count": len(triangles),
            "stable_face_ids": [
                hashlib.sha256(
                    f"{geometry_hash}:{index}:{','.join(str(int(value)) for value in triangle)}".encode()
                ).hexdigest()[:20]
                for index, triangle in enumerate(triangles)
            ],
        },
        "camera_poses": [
            {
                "view": view.view,
                "projection": "orthographic",
                "axes": view.projection_axes,
            }
            for view in views
        ],
        "silhouette": {
            view.view: {"projected_bounds": view.projected_bounds}
            for view in views
        },
        "metric_depth": {
            view.view: {"range_m": view.depth_range}
            for view in views
        },
        "surface_normals": triangle_normals(vertices, triangles),
        "floor_guides_m": _floor_guides(float(minimum[2]), float(maximum[2])),
        "facade_planes": _facade_planes(minimum, maximum),
        "geometry_mutation_allowed": False,
    }
    condition_path = root / "condition-pack.json"
    _write_json_atomic(condition_path, condition_pack)
    manifest_path = root / "manifest.json"
    bundle = ElevationBundle(
        execution_id=execution_id,
        program_hash=program_hash,
        geometry_hash=geometry_hash,
        output_directory=str(root),
        manifest_path=str(manifest_path),
        condition_pack_path=str(condition_path),
        views=views,
        condition_pack=condition_pack,
    )
    payload = bundle.to_dict()
    _write_json_atomic(manifest_path, payload)
    return payload


def _floor_guides(minimum_z: float, maximum_z: float, interval: float = 3.3) -> list[float]:
    guides: list[float] = []
    value = minimum_z
    while value <= maximum_z + 1e-9 and len(guides) < 128:
        guides.append(round(value, 6))
        value += interval
    if not guides or guides[-1] < maximum_z:
        guides.append(round(maximum_z, 6))
    return guides


def _facade_planes(minimum: Any, maximum: Any) -> list[dict[str, Any]]:
    minx, miny, minz = (float(value) for value in minimum)
    maxx, maxy, maxz = (float(value) for value in maximum)
    return [
        {"view": "front", "normal": [0, -1, 0], "origin": [minx, miny, minz], "extent": [maxx - minx, maxz - minz]},
        {"view": "right", "normal": [1, 0, 0], "origin": [maxx, miny, minz], "extent": [maxy - miny, maxz - minz]},
        {"view": "back", "normal": [0, 1, 0], "origin": [maxx, maxy, minz], "extent": [maxx - minx, maxz - minz]},
        {"view": "left", "normal": [-1, 0, 0], "origin": [minx, maxy, minz], "extent": [maxy - miny, maxz - minz]},
    ]


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(f"{path.suffix}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


__all__ = ["generate_elevation_bundle"]
