"""Typed source-geometry objects for ARR MAAS grammar generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shapely.geometry import Polygon, mapping


@dataclass(frozen=True)
class VerbTrace:
    verb: str
    params: dict[str, Any]
    status: str
    footprint_area_m2: float
    upper_area_m2: float | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "verb": self.verb,
            "params": self.params,
            "status": self.status,
            "footprint_area_m2": round(self.footprint_area_m2, 2),
        }
        if self.upper_area_m2 is not None:
            data["upper_area_m2"] = round(self.upper_area_m2, 2)
        if self.note:
            data["note"] = self.note
        return data


@dataclass(frozen=True)
class SourceVolume:
    role: str
    footprint: Polygon
    bottom_fraction: float
    top_fraction: float
    verb: str

    def signature(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "verb": self.verb,
            "bottom_fraction": round(self.bottom_fraction, 3),
            "top_fraction": round(self.top_fraction, 3),
            "area_m2": round(float(self.footprint.area), 2),
            "geometry_utm": mapping(self.footprint),
            "geometry_crs": "EPSG:32652",
        }


@dataclass(frozen=True)
class SourceSurface:
    role: str
    volume_role: str
    verb: str
    surface_type: str
    vertices_m: tuple[tuple[float, float, float], ...]
    operator: str = "extrude"
    semantic_patch_id: str = ""

    def signature(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "volume_role": self.volume_role,
            "verb": self.verb,
            "surface_type": self.surface_type,
            "vertex_count": len(self.vertices_m),
            "vertices_m": [
                [round(x, 3), round(y, 3), round(z, 3)]
                for x, y, z in self.vertices_m
            ],
            "operator": self.operator,
            "semantic_patch_id": self.semantic_patch_id or f"{self.volume_role}:{self.surface_type}",
        }


@dataclass(frozen=True)
class SourceMass:
    name: str
    footprint: Polygon
    upper_footprint: Polygon | None = None
    lower_floor_fraction: float | None = None
    volumes: tuple[SourceVolume, ...] = ()
    surfaces: tuple[SourceSurface, ...] = ()
    verb_trace: tuple[VerbTrace, ...] = ()
    notes: tuple[str, ...] = ()
    status: str = "compiled"
    fallback_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def signature(self) -> dict[str, Any]:
        areas = [float(volume.footprint.area) for volume in self.volumes]
        ground_area = float(self.footprint.area)
        upper_area = float(self.upper_footprint.area) if self.upper_footprint is not None else None
        centroid = self.footprint.centroid
        parameter_provenance = self.metadata.get("parameter_provenance", [])
        parameter_default_count = int(self.metadata.get("parameter_default_count", 0) or 0)
        parameter_authored_count = sum(
            1 for item in parameter_provenance
            if isinstance(item, dict) and not item.get("used_default")
        )
        parameter_total = parameter_default_count + parameter_authored_count
        rule_evidence = self.metadata.get("rule_evidence")
        if not isinstance(rule_evidence, dict):
            rule_evidence = {}
        rule_prior_param_count = int(rule_evidence.get("rule_prior_param_count", 0) or 0)
        llm_authored_param_count = int(rule_evidence.get("llm_authored_param_count", 0) or 0)
        rule_param_total = rule_prior_param_count + llm_authored_param_count
        primary_language = str(self.metadata.get("primary_language") or "")
        secondary_language = str(self.metadata.get("secondary_language") or "")
        reference_basis = str(self.metadata.get("reference_basis") or "")
        formal_principle = str(self.metadata.get("formal_principle") or "")
        dominant_gesture = str(self.metadata.get("dominant_gesture") or "")
        massing_genome = self.metadata.get("massing_genome")
        if not isinstance(massing_genome, dict):
            massing_genome = {}
        massing_genome_circuit = self.metadata.get("massing_genome_circuit")
        if not isinstance(massing_genome_circuit, dict):
            massing_genome_circuit = {}
        component_graph = self.metadata.get("component_graph")
        if not isinstance(component_graph, dict):
            component_graph = {}
        graph_materialization_evidence = self.metadata.get("graph_materialization_evidence")
        if not isinstance(graph_materialization_evidence, dict):
            graph_materialization_evidence = {}
        coherence_evidence = self.metadata.get("coherence_evidence")
        if not isinstance(coherence_evidence, dict):
            coherence_evidence = {}
        continuous_surface_evidence = self.metadata.get("continuous_surface_evidence")
        if not isinstance(continuous_surface_evidence, dict):
            continuous_surface_evidence = {}
        geometry_program = self.metadata.get("geometry_program")
        if not isinstance(geometry_program, dict):
            geometry_program = {}
        geometry_graph_snapshot = self.metadata.get("geometry_graph_snapshot")
        if not isinstance(geometry_graph_snapshot, dict):
            geometry_graph_snapshot = {}
        geometry_program_bridge_evidence = self.metadata.get("geometry_program_bridge_evidence")
        if not isinstance(geometry_program_bridge_evidence, dict):
            geometry_program_bridge_evidence = {}
        program_space_zones = self.metadata.get("program_space_zones")
        if not isinstance(program_space_zones, list):
            program_space_zones = []
        program_role_integration_evidence = self.metadata.get("program_role_integration_evidence")
        if not isinstance(program_role_integration_evidence, dict):
            program_role_integration_evidence = {}
        program_section_graph_evidence = self.metadata.get("program_section_graph_evidence")
        if not isinstance(program_section_graph_evidence, dict):
            program_section_graph_evidence = {}
        site_frame_evidence = self.metadata.get("site_frame_evidence")
        if not isinstance(site_frame_evidence, dict):
            site_frame_evidence = {}
        secondary_family = str(self.metadata.get("secondary_family") or "")
        if not primary_language:
            rule_descriptor = rule_evidence.get("research_diversity_descriptor")
            if isinstance(rule_descriptor, dict):
                primary_language = str(rule_descriptor.get("mass_language") or "")
        if not primary_language:
            primary_language = str(self.metadata.get("family") or "")
        if not secondary_language:
            secondary_language = str(
                massing_genome.get("vertical_strategy")
                or massing_genome.get("void_strategy")
                or massing_genome.get("connector_strategy")
                or ""
            )
        composition_layer_roles = [
            volume.role
            for volume in self.volumes
            if str(volume.role).startswith("secondary_")
        ]
        primitive_roles = {
            "polygonal": [
                volume.role
                for volume in self.volumes
                if str(volume.role).startswith("polygonal_")
            ],
            "curvilinear": [
                volume.role
                for volume in self.volumes
                if str(volume.role).startswith("curvilinear_")
            ],
            "freeform": [
                volume.role
                for volume in self.volumes
                if str(volume.role).startswith("freeform_")
            ],
        }
        principle_primitive_roles = {
            "torqued_stack": ("curvilinear_torque_axis",),
            "folded_section": ("polygonal_folded_plane",),
            "stacked_shifted_platforms": ("polygonal_shifted_platform",),
            "split_bridge_connector": ("polygonal_bridge_cut",),
            "carved_monolith": ("freeform_carved_void",),
            "carved_atrium": ("freeform_atrium_void",),
            "continuous_ribbon_field": ("curvilinear_continuous_ribbon",),
        }.get(str(formal_principle), ())
        for primitive_role in principle_primitive_roles:
            bucket = "freeform" if primitive_role.startswith("freeform_") else (
                "curvilinear" if primitive_role.startswith("curvilinear_") else "polygonal"
            )
            if primitive_role not in primitive_roles[bucket]:
                primitive_roles[bucket].append(primitive_role)
        composition_rule = ""
        if primary_language and secondary_language and secondary_language != "legal_envelope_fit":
            composition_rule = f"{primary_language}+{secondary_language}"
        ambition = self.metadata.get("architectural_ambition_evidence")
        if not isinstance(ambition, dict):
            ambition = {}
        ambition_evidence = {
            "schema_version": "arr.maas.architectural_ambition.v1",
            "reference_basis": reference_basis,
            "formal_principle": formal_principle,
            "dominant_gesture": dominant_gesture,
            "has_reference_basis": bool(reference_basis),
            "has_formal_principle": bool(formal_principle),
            "has_dominant_gesture": bool(dominant_gesture),
            **ambition,
        }
        if not ambition_evidence.get("architecture_grade_pass"):
            ambition_evidence["architecture_grade_pass"] = bool(
                ambition_evidence["has_formal_principle"]
                and ambition_evidence["has_dominant_gesture"]
                and len(composition_layer_roles) >= 1
            )
        raw_surface_count = len(self.surfaces)
        has_profiled_surfaces = any(surface.surface_type.startswith("profiled_") for surface in self.surfaces)
        logical_surface_count = len({
            surface.semantic_patch_id or f"{surface.volume_role}:{surface.surface_type}"
            for surface in self.surfaces
        })
        effective_surface_count = logical_surface_count if has_profiled_surfaces else raw_surface_count
        return {
            "schema_version": "arr.maas.source_geometry.signature.v1",
            "status": self.status,
            "family": self.metadata.get("family"),
            "primary_language": primary_language,
            "secondary_language": secondary_language,
            "reference_basis": reference_basis,
            "formal_principle": formal_principle,
            "dominant_gesture": dominant_gesture,
            "massing_genome": massing_genome,
            "massing_genome_circuit": massing_genome_circuit,
            "component_graph": component_graph,
            "graph_materialization_evidence": graph_materialization_evidence,
            "coherence_evidence": coherence_evidence,
            "continuous_surface_evidence": continuous_surface_evidence,
            "geometry_program": geometry_program,
            "geometry_graph_snapshot": geometry_graph_snapshot,
            "geometry_program_bridge_evidence": geometry_program_bridge_evidence,
            "program_space_zones": program_space_zones,
            "program_role_integration_evidence": program_role_integration_evidence,
            "program_section_graph_evidence": program_section_graph_evidence,
            "site_frame_evidence": site_frame_evidence,
            "architectural_ambition_evidence": ambition_evidence,
            "secondary_family": secondary_family,
            "composition_rule": composition_rule,
            "composition_layer_roles": composition_layer_roles,
            "composition_layer_count": len(composition_layer_roles),
            "source_primitive_roles": primitive_roles,
            "source_primitive_count": sum(len(roles) for roles in primitive_roles.values()),
            "volume_count": len(self.volumes),
            "surface_count": raw_surface_count,
            "logical_surface_count": logical_surface_count,
            "effective_surface_count": effective_surface_count,
            "ground_area_m2": round(ground_area, 2),
            "upper_area_m2": round(upper_area, 2) if upper_area is not None else None,
            "upper_to_ground_ratio": round(upper_area / ground_area, 4) if upper_area and ground_area > 0 else None,
            "area_profile_m2": [round(area, 2) for area in areas],
            "verb_profile": [trace.verb for trace in self.verb_trace if trace.verb != "base"],
            "surface_roles": sorted({surface.role for surface in self.surfaces}),
            "centroid": [round(float(centroid.x), 2), round(float(centroid.y), 2)],
            "asymmetry_hint": self.metadata.get("asymmetry_hint"),
            "parameter_provenance": parameter_provenance,
            "parameter_default_count": parameter_default_count,
            "parameter_authored_count": parameter_authored_count,
            "parameter_default_ratio": round(parameter_default_count / parameter_total, 4) if parameter_total else 0.0,
            "rule_evidence": rule_evidence,
            "rule_prior_param_count": rule_prior_param_count,
            "llm_authored_param_count": llm_authored_param_count,
            "rule_prior_param_ratio": round(rule_prior_param_count / rule_param_total, 4) if rule_param_total else 0.0,
            "invalid_rule_param_count": int(rule_evidence.get("invalid_rule_param_count", 0) or 0),
        }

    def source_volume_signatures(self) -> tuple[dict[str, Any], ...]:
        return tuple(volume.signature() for volume in self.volumes)

    def source_surface_signatures(self) -> tuple[dict[str, Any], ...]:
        return tuple(surface.signature() for surface in self.surfaces)
