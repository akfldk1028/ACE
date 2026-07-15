"""Diagram-derived semantics for the architect-supplied BOOK.

The BOOK is not a flat list of attractive labels.  Each base operative is a
three-part grammar: choose a relative base volume and orientation, perform one
spatial action, then explore bounded variations of the action.  This module
keeps that evidence separate from parcel coordinates and compiler geometry.
"""

from __future__ import annotations

from dataclasses import dataclass


BASE_VOLUME_FRACTIONS: tuple[tuple[str, float], ...] = (
    ("1/1", 1.0),
    ("3/8", 3.0 / 8.0),
    ("1/2", 1.0 / 2.0),
    ("1/4", 1.0 / 4.0),
    ("1/8", 1.0 / 8.0),
    ("1/16", 1.0 / 16.0),
)


@dataclass(frozen=True)
class BookOperationSemantics:
    action: str
    input_topology: str
    output_topology: str
    variation_parameters: tuple[str, ...]
    orientation_modes: tuple[str, ...] = ("long_axis", "short_axis", "vertical")

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "input_topology": self.input_topology,
            "output_topology": self.output_topology,
            "procedure": [
                "select_relative_base_volume_and_orientation",
                self.action,
                "evaluate_bounded_variations_without_changing_the_operative_identity",
            ],
            "variation_parameters": list(self.variation_parameters),
            "orientation_modes": list(self.orientation_modes),
            "base_volume_fractions": [label for label, _fraction in BASE_VOLUME_FRACTIONS],
            "evidence_kind": "diagram_derived",
        }


# These records transcribe the operation shown on BOOK pp.6-37.  They describe
# intent and legal mutation axes; they deliberately contain no site coordinate
# or named-precedent footprint.
OPERATION_SEMANTICS: dict[str, BookOperationSemantics] = {
    "expand": BookOperationSemantics("extend one boundary or sectional face outward", "single_volume", "single_enlarged_volume", ("factor", "axis", "upper_ratio")),
    "extrude": BookOperationSemantics("project a selected face or region along an axis", "single_volume", "single_extended_volume", ("axis", "length", "size")),
    "inflate": BookOperationSemantics("displace the envelope outward to form a swollen crown", "single_volume", "single_profiled_volume", ("factor", "upper_ratio")),
    "branch": BookOperationSemantics("grow secondary arms from a primary trunk", "single_volume", "connected_multi_arm_volume", ("trunk_ratio", "arm_ratio", "angle")),
    "merge": BookOperationSemantics("fuse separate volumes into one continuous body", "multiple_volumes", "single_fused_volume", ("axis", "gap_ratio", "unit_scale")),
    "nest": BookOperationSemantics("place a smaller volume concentrically within a host", "multiple_volumes", "nested_volumes", ("inner_scale", "upper_ratio")),
    "offset": BookOperationSemantics("duplicate and translate a related volume", "multiple_volumes", "offset_related_volumes", ("axis", "distance_ratio", "other_scale")),
    "bend": BookOperationSemantics("deflect a continuous longitudinal axis into a bend", "single_volume", "single_bent_volume", ("axis", "angle", "curvature", "width_gradient")),
    "skew": BookOperationSemantics("obliquely displace faces while preserving continuity", "single_volume", "single_skewed_volume", ("axis", "angle", "upper_ratio")),
    "split": BookOperationSemantics("divide one volume along a selected axis", "single_volume", "separated_related_volumes", ("axis", "gap_ratio", "bridge_ratio")),
    "twist": BookOperationSemantics("rotate successive sections around the vertical axis", "single_volume", "single_twisted_volume", ("angle", "upper_ratio")),
    "interlock": BookOperationSemantics("cross and lock multiple bars through a shared zone", "multiple_volumes", "interlocked_volumes", ("axis", "angle", "bar_ratio", "distance_ratio")),
    "intersect": BookOperationSemantics("retain the spatial crossing of multiple volumes", "multiple_volumes", "intersecting_volume", ("angle", "factor")),
    "lift": BookOperationSemantics("raise a volume to create a continuous undercroft", "multiple_volumes", "elevated_volume_and_ground_gap", ("upper_ratio", "lower_floor_fraction")),
    "lodge": BookOperationSemantics("insert a guest volume partly into a host", "multiple_volumes", "host_with_lodged_guest", ("axis", "distance_ratio", "guest_scale")),
    "overlap": BookOperationSemantics("partially superpose related volumes in plan or section", "multiple_volumes", "overlapping_volumes", ("axis", "slab_ratio", "shift_ratio", "vertical_overlap")),
    "rotate": BookOperationSemantics("rotate a related volume about a shared center", "multiple_volumes", "rotated_related_volumes", ("angle", "factor")),
    "shift": BookOperationSemantics("translate a related volume without rotating it", "multiple_volumes", "shifted_related_volumes", ("axis", "distance_ratio")),
    "carve": BookOperationSemantics("remove a bounded recess from an exposed side", "single_volume", "single_recessed_volume", ("side", "width_ratio", "depth_ratio")),
    "compress": BookOperationSemantics("contract the volume along one selected axis", "single_volume", "single_compressed_volume", ("axis", "factor")),
    "fracture": BookOperationSemantics("open a directional break through the volume", "single_volume", "fractured_related_parts", ("axis", "gap_ratio", "angle")),
    "grade": BookOperationSemantics("subtract progressively to form a graded section", "single_volume", "single_graded_volume", ("side", "width_ratio", "depth_ratio")),
    "notch": BookOperationSemantics("remove a compact piece from one corner", "single_volume", "single_notched_volume", ("corner", "ratio")),
    "pinch": BookOperationSemantics("contract an intermediate waist while retaining the ends", "single_volume", "single_pinched_volume", ("axis", "waist_ratio", "depth_ratio")),
    "shear": BookOperationSemantics("laterally displace one section to create an oblique cut", "single_volume", "single_sheared_volume", ("axis", "angle")),
    "taper": BookOperationSemantics("reduce successive plan sections toward one end or top", "single_volume", "single_tapered_volume", ("x_ratio", "y_ratio", "top_shift_x_ratio", "top_shift_y_ratio")),
    "embed": BookOperationSemantics("subtract the overlap made by a guest embedded in a host", "multiple_volumes", "host_with_embedded_void", ("guest_scale", "position", "distance_ratio")),
    "extract": BookOperationSemantics("remove and expose an internal piece through a mouth", "multiple_volumes", "host_and_extracted_void", ("side", "ratio", "distance_ratio")),
    "inscribe": BookOperationSemantics("subtract a geometrically related inner volume", "multiple_volumes", "inscribed_shell_or_court", ("ratio", "open_side")),
    "puncture": BookOperationSemantics("subtract repeated compact openings through the mass", "multiple_volumes", "perforated_volume", ("axis", "n", "spacing_ratio", "ratio")),
}


def semantics_for(verb: str) -> BookOperationSemantics:
    try:
        return OPERATION_SEMANTICS[verb]
    except KeyError as exc:
        raise ValueError(f"BOOK semantics missing for {verb!r}") from exc


__all__ = ["BASE_VOLUME_FRACTIONS", "BookOperationSemantics", "OPERATION_SEMANTICS", "semantics_for"]
