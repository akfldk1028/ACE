"""Typed, serializable contracts for deterministic MASS elevations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ElevationViewArtifact:
    view: str
    path: str
    preview_url: str
    sha256: str
    width_px: int
    height_px: int
    projection_axes: dict[str, list[float]]
    view_matrix4: list[list[float]]
    projected_bounds: list[list[float]]
    depth_range: list[float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ElevationBundle:
    execution_id: str
    program_hash: str
    geometry_hash: str
    output_directory: str
    manifest_path: str
    condition_pack_path: str
    views: tuple[ElevationViewArtifact, ...]
    condition_pack: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.elevation_agent.bundle.v1",
            "status": "generated",
            "execution_id": self.execution_id,
            "program_hash": self.program_hash,
            "geometry_hash": self.geometry_hash,
            "output_directory": self.output_directory,
            "manifest_path": self.manifest_path,
            "condition_pack_path": self.condition_pack_path,
            "view_count": len(self.views),
            "views": [view.to_dict() for view in self.views],
            "condition_pack": self.condition_pack,
        }


__all__ = ["ElevationBundle", "ElevationViewArtifact"]
