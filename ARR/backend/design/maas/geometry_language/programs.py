"""Executable geometry programs for the architectural mass vocabulary.

These are operator-coverage probes and reference-language demonstrations, not
parcel templates or copies of completed buildings.  Dimensions are local and
normalized enough to be scaled/oriented by the site/program graph later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .ast import GeometryNode, GeometryProgram
from .book_chassis_compatibility import SPLIT_WING_RELATION_CONTRACT


@dataclass
class GeometryProgramBuilder:
    name: str
    nodes: list[GeometryNode] = field(default_factory=list)
    _counter: int = 0

    def add(
        self,
        kind: str,
        operator: str,
        *,
        inputs: tuple[str, ...] = (),
        parameters: dict[str, Any] | None = None,
        semantic_role: str = "",
        node_id: str = "",
    ) -> str:
        self._counter += 1
        resolved_id = node_id or f"n{self._counter:02d}_{operator}"
        self.nodes.append(GeometryNode(
            id=resolved_id,
            kind=kind,
            operator=operator,
            inputs=inputs,
            parameters=parameters or {},
            semantic_role=semantic_role,
            provenance={"source": "executable_language_probe"},
        ))
        return resolved_id

    def build(self, root_id: str, **metadata: Any) -> GeometryProgram:
        # A builder may be reused to inspect an intermediate result after later
        # nodes have already been declared.  Emit only the ancestry of the
        # requested root so the resulting SolidNode program cannot advertise
        # semantic roles that its compiled geometry does not consume.
        node_map = {node.id: node for node in self.nodes}
        reachable: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in reachable or node_id not in node_map:
                return
            for input_id in node_map[node_id].inputs:
                visit(input_id)
            reachable.add(node_id)

        visit(root_id)
        nodes = tuple(node for node in self.nodes if node.id in reachable)
        return GeometryProgram(nodes, root_id, self.name, metadata=metadata)


def architectural_shape_programs() -> tuple[GeometryProgram, ...]:
    """Return 18 distinct core/macro programs matching the requested families."""
    programs = [
        _bent_linear_mass(),
        _radial_fan_mass(),
        _l_mass_union(),
        _u_mass(),
        _courtyard_mass(),
        _attached_volume_mass(),
        _overlapping_mass(),
        _setback_mass(),
        _cross_mass(),
        _tapered_mass(),
        _leaning_tower(),
        _notched_mass(),
        _diagonal_slice_mass(),
        _cut_corner_mass(),
        _lofted_top_bottom_mass(),
        _swept_curved_bar(),
        _split_bridge_mass(),
        _twisted_mass(),
    ]
    return tuple(programs)


def reference_language_programs() -> dict[str, GeometryProgram]:
    """Abstract the three supplied photos into transferable mass operations."""
    return {
        "songeun_oblique_carved_monolith": _songeun_language(),
        "amorepacific_carved_cantilever_cube": _amorepacific_language(),
        "photo_museum_lifted_oblique_envelope": _photo_museum_language(),
    }


def l_mass_difference_program() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_03_l_mass_difference")
    base = b.add("primitive", "box", parameters={"width": 8, "depth": 8, "height": 3}, semantic_role="main")
    cutter = b.add("primitive", "box", parameters={"width": 5, "depth": 5, "height": 4}, semantic_role="void")
    moved = b.add("transform", "translate", inputs=(cutter,), parameters={"vector": [3, 3, -0.5]})
    root = b.add("boolean", "difference", inputs=(base, moved), semantic_role="main")
    return b.build(root, family="l_mass", canonical_alternative="difference")


def _bent_linear_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_01_bent_linear_mass")
    # A bent building bar must remain occupiable after the normalized host fit.
    # The old 1:5 ribbon projected below the base-stage capacity floor and read
    # as a sculptural strip rather than a low-rise chassis.
    base = b.add("primitive", "box", parameters={"width": 14, "depth": 3.8, "height": 3.5}, semantic_role="main")
    root = b.add("modifier", "bend", inputs=(base,), parameters={"axis": "x", "angle_degrees": 42, "subdivisions": 4}, semantic_role="main")
    return b.build(root, family="bent_linear_mass")


def _radial_fan_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_02_radial_fan_mass")
    # Three occupiable wings meet a compact hub.  The former five thin strips
    # produced a starburst perimeter (P^2/4piA=7.77, hull excess=2.10), so the
    # exact polygon-quality gate correctly rejected every projected descendant.
    # This is still a radial relation, but now reads as one connected pinwheel
    # chassis rather than repeated sculpture fragments.
    wing = b.add(
        "primitive", "box",
        parameters={"width": 11, "depth": 4.0, "height": 3.2},
        semantic_role="wing",
    )
    aligned_wing = b.add(
        "transform", "translate", inputs=(wing,),
        parameters={"vector": [0.0, -2.0, 0]},
    )
    wings = b.add(
        "pattern", "radial_array", inputs=(aligned_wing,),
        parameters={"count": 3, "total_angle_degrees": 120, "pivot": [0, 0, 0]},
        semantic_role="wing",
    )
    hub = b.add(
        "primitive", "box",
        parameters={"width": 5.0, "depth": 5.0, "height": 3.2},
        semantic_role="main",
    )
    centered_hub = b.add(
        "transform", "translate", inputs=(hub,),
        parameters={"vector": [-2.5, -2.5, 0]},
    )
    root = b.add("boolean", "union", inputs=(centered_hub, wings), semantic_role="main")
    return b.build(root, family="radial_fan")


def _l_mass_union() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_03_l_mass_union")
    long = b.add("primitive", "box", parameters={"width": 8, "depth": 3, "height": 3}, semantic_role="wing")
    short = b.add("primitive", "box", parameters={"width": 3, "depth": 8, "height": 3}, semantic_role="wing")
    root = b.add("boolean", "union", inputs=(long, short), semantic_role="main")
    return b.build(root, family="l_mass", canonical_alternative="union")


def _u_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_04_u_mass")
    left = b.add("primitive", "box", parameters={"width": 2.2, "depth": 9, "height": 3}, semantic_role="wing")
    right0 = b.add("primitive", "box", parameters={"width": 2.2, "depth": 9, "height": 3}, semantic_role="wing")
    right = b.add("transform", "translate", inputs=(right0,), parameters={"vector": [7.8, 0, 0]})
    back = b.add("primitive", "box", parameters={"width": 10, "depth": 2.2, "height": 3}, semantic_role="wing")
    root = b.add("boolean", "union", inputs=(left, right, back), semantic_role="main")
    return b.build(root, family="u_mass")


def _courtyard_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_05_courtyard_mass")
    base = b.add("primitive", "box", parameters={"width": 10, "depth": 10, "height": 4}, semantic_role="main")
    root = b.add("macro", "courtyard", inputs=(base,), parameters={"margin_ratio": 0.24}, semantic_role="main")
    return b.build(root, family="courtyard")


def _attached_volume_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_06_attached_volume")
    main = b.add("primitive", "box", parameters={"width": 9, "depth": 6, "height": 4}, semantic_role="main")
    annex0 = b.add("primitive", "box", parameters={"width": 3, "depth": 2.5, "height": 2.5}, semantic_role="support")
    annex = b.add("transform", "translate", inputs=(annex0,), parameters={"vector": [8, 1.75, 0.5]})
    root = b.add("composition", "attach", inputs=(main, annex), semantic_role="main")
    return b.build(root, family="attached_volume")


def _overlapping_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_07_overlapping_rotated_mass")
    first = b.add("primitive", "box", parameters={"width": 9, "depth": 3, "height": 3}, semantic_role="main")
    second0 = b.add("primitive", "box", parameters={"width": 8, "depth": 3, "height": 3}, semantic_role="support")
    second1 = b.add("transform", "rotate", inputs=(second0,), parameters={"axis": "z", "angle_degrees": 28, "pivot": [4, 1.5, 0]})
    second = b.add("transform", "translate", inputs=(second1,), parameters={"vector": [2, 1.5, 1.4]})
    root = b.add("boolean", "union", inputs=(first, second), semantic_role="main")
    return b.build(root, family="overlapping_mass")


def _setback_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_08_setback_mass")
    base = b.add("primitive", "box", parameters={"width": 10, "depth": 9, "height": 12}, semantic_role="main")
    root = b.add("macro", "setback", inputs=(base,), parameters={"levels": 4, "setback_ratio": 0.12}, semantic_role="main")
    return b.build(root, family="setback")


def _cross_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_09_cross_mass")
    # Preserve the cross void/wing figure without making each arm a thin
    # pavilion.  This normalized 0.31 arm ratio clears the same measured
    # capacity contract used by every other chassis; no parcel dimension is
    # encoded here.
    bar = b.add("primitive", "box", parameters={"width": 11, "depth": 3.4, "height": 3.2}, semantic_role="main")
    root = b.add("macro", "cross_mass", inputs=(bar,), parameters={"angle_degrees": 90}, semantic_role="main")
    return b.build(root, family="cross_mass")


def _tapered_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_10_tapered_mass")
    tower = b.add("primitive", "box", parameters={"width": 7, "depth": 6, "height": 14}, semantic_role="main")
    root = b.add("macro", "tapered_tower", inputs=(tower,), parameters={"axis": "z", "end_scale": [0.46, 0.66], "subdivisions": 3}, semantic_role="main")
    return b.build(root, family="tapered_tower")


def _leaning_tower() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_11_leaning_tower")
    tower = b.add("primitive", "box", parameters={"width": 5, "depth": 5, "height": 16}, semantic_role="main")
    root = b.add("macro", "leaning_tower", inputs=(tower,), parameters={"direction": "x", "amount": 0.2}, semantic_role="main")
    return b.build(root, family="leaning_tower")


def _notched_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_12_notched_mass")
    base = b.add("primitive", "box", parameters={"width": 10, "depth": 7, "height": 5}, semantic_role="main")
    root = b.add("macro", "notch", inputs=(base,), parameters={"corner": "se", "ratio": 0.28, "height_ratio": 0.72}, semantic_role="main")
    return b.build(root, family="notch")


def _diagonal_slice_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_13_diagonal_slice")
    base = b.add("primitive", "box", parameters={"width": 10, "depth": 7, "height": 8}, semantic_role="main")
    root = b.add("modifier", "slice", inputs=(base,), parameters={"normal": [1, 0, -1], "offset": -3, "keep_side": "positive"}, semantic_role="main")
    return b.build(root, family="diagonal_slice")


def _cut_corner_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_14_cut_corner_polyhedron")
    base = b.add("primitive", "box", parameters={"width": 10, "depth": 8, "height": 6}, semantic_role="main")
    root = b.add("macro", "cut_corner", inputs=(base,), parameters={"corner": "ne", "ratio": 0.24}, semantic_role="main")
    return b.build(root, family="cut_corner")


def _lofted_top_bottom_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_15_lofted_top_bottom_mass")
    profiles = [
        {"z": 0, "points": [[0, 0], [10, 0], [10, 8], [0, 8]]},
        {"z": 5, "points": [[0.7, 0.4], [9.6, 0.6], [9.1, 7.5], [0.9, 7.2]]},
        {"z": 10, "points": [[2.2, 1.4], [8.4, 1.2], [8, 6.5], [2.6, 6.7]]},
    ]
    root = b.add("primitive", "loft", parameters={"profiles": profiles}, semantic_role="main")
    return b.build(root, family="lofted_envelope")


def _swept_curved_bar() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_16_swept_curved_bar")
    root = b.add("primitive", "sweep", parameters={
        "profile_width": 2.4,
        "profile_height": 3.4,
        "path": [[0, 0, 0], [3, 0.2, 0], [6, 1.1, 0], [8.5, 2.8, 0], [10.5, 5.2, 0]],
    }, semantic_role="main")
    return b.build(root, family="swept_bar")


def _split_bridge_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_17_split_wing_bridge")
    base = b.add("primitive", "box", parameters={"width": 12, "depth": 7, "height": 6}, semantic_role="main")
    # Split the short axis so two long, calm wings frame an occupiable public
    # gap.  Splitting the long axis produced two toy blocks whose small bridge
    # read as an afterthought in every view.
    root = b.add("macro", "split_wing", inputs=(base,), parameters={
        "axis": "y",
        "gap_ratio": SPLIT_WING_RELATION_CONTRACT.default_public_gap_ratio,
        "bridge": True,
        "height_ratio": 0.62,
        "height": 1.2,
    }, semantic_role="main")
    return b.build(root, family="split_bridge")


def _twisted_mass() -> GeometryProgram:
    b = GeometryProgramBuilder("shape_18_twisted_mass")
    tower = b.add("primitive", "box", parameters={"width": 6, "depth": 4.5, "height": 13}, semantic_role="main")
    # Two controlled vertical bands retain a calm torsion while leaving surface
    # budget for the later BOOK operation and program threshold. Four subdivisions
    # multiplied into 98 vertices before those downstream operations and 21/22
    # neighborhood descendants failed the unchanged clean-surface gate. An
    # 18-degree turn with two bands stays connected under all three program
    # projections while avoiding another faceted pseudo-sculpture.
    root = b.add("modifier", "twist", inputs=(tower,), parameters={"axis": "z", "angle_degrees": 18, "subdivisions": 2}, semantic_role="main")
    return b.build(root, family="twisted_mass")


def _songeun_language() -> GeometryProgram:
    b = GeometryProgramBuilder("reference_songeun_oblique_carved_monolith")
    envelope = b.add("primitive", "loft", parameters={"profiles": [
        {"z": 0, "points": [[0, 0], [12, 0], [12, 8], [0, 8]]},
        {"z": 14, "points": [[0.6, 0.2], [10.6, 0.6], [11.2, 7.6], [0.8, 7.8]]},
        {"z": 28, "points": [[3.2, 1.0], [8.4, 1.6], [9.4, 7.0], [2.8, 7.2]]},
    ]}, semantic_role="main")
    cutter0 = b.add("primitive", "wedge", parameters={"width": 4.8, "depth": 10, "start_height": 1.0, "end_height": 10.5}, semantic_role="public_void")
    cutter = b.add("transform", "translate", inputs=(cutter0,), parameters={"vector": [4.8, -1, -0.2]})
    root = b.add("boolean", "difference", inputs=(envelope, cutter), semantic_role="main")
    return b.build(root, family="songeun_oblique_carved_monolith", reference_basis="supplied_photo", transferable_principle="oblique tapered monolith plus triangular carved entry")


def _amorepacific_language() -> GeometryProgram:
    b = GeometryProgramBuilder("reference_amorepacific_carved_cantilever_cube")
    cube = b.add("primitive", "box", parameters={"width": 24, "depth": 24, "height": 24}, semantic_role="main")
    void0 = b.add("primitive", "box", parameters={"width": 14, "depth": 13, "height": 13}, semantic_role="public_void")
    void = b.add("transform", "translate", inputs=(void0,), parameters={"vector": [5, -1, 5]})
    carved = b.add("boolean", "difference", inputs=(cube, void), semantic_role="main")
    root = b.add("macro", "cantilever", inputs=(carved,), parameters={"start_ratio": 0.66, "vector": [1.4, 0, 0]}, semantic_role="main")
    return b.build(root, family="amorepacific_carved_cantilever_cube", reference_basis="supplied_photo", transferable_principle="carved civic cube plus suspended upper plate")


def _photo_museum_language() -> GeometryProgram:
    b = GeometryProgramBuilder("reference_photo_museum_lifted_oblique_envelope")
    base = b.add("primitive", "box", parameters={"width": 18, "depth": 12, "height": 18}, semantic_role="main")
    leaned = b.add("macro", "leaning_tower", inputs=(base,), parameters={"direction": "x", "amount": -0.11}, semantic_role="main")
    undercut0 = b.add("primitive", "wedge", parameters={"width": 10, "depth": 14, "start_height": 1, "end_height": 7.5}, semantic_role="public_void")
    undercut = b.add("transform", "translate", inputs=(undercut0,), parameters={"vector": [-1, -1, -0.2]})
    root = b.add("boolean", "difference", inputs=(leaned, undercut), semantic_role="main")
    return b.build(root, family="photo_museum_lifted_oblique_envelope", reference_basis="supplied_photo", transferable_principle="continuous oblique envelope with lifted diagonal undercut")


__all__ = [
    "GeometryProgramBuilder",
    "architectural_shape_programs",
    "l_mass_difference_program",
    "reference_language_programs",
]
