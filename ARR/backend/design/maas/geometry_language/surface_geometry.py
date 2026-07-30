"""Kernel-independent bounded surface values for the MASS geometry language."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Any, TypeAlias

Vec3: TypeAlias = tuple[float, float, float]
Bounds: TypeAlias = tuple[float, float, float, float, float, float]

_BOUNDS_TOLERANCE = 1e-7
_POINT_TOLERANCE = 1e-12
_SUPPORTED_HOST_FACES = frozenset(
    {"east", "west", "north", "south", "top", "bottom"}
)


@dataclass(frozen=True)
class BoundedSurface:
    """A deterministic intermediate surface with no geometry-kernel state."""

    operator: str
    sections: tuple[tuple[Vec3, ...], ...]
    source_bounds: Bounds

    def __post_init__(self) -> None:
        object.__setattr__(self, "operator", str(self.operator))
        object.__setattr__(
            self,
            "sections",
            tuple(
                tuple(
                    tuple(float(coordinate) for coordinate in point)
                    for point in section
                )
                for section in self.sections
            ),
        )
        object.__setattr__(
            self,
            "source_bounds",
            tuple(float(value) for value in self.source_bounds),
        )

    def validate(self) -> tuple[str, ...]:
        """Return stable error codes for geometry that cannot form a shell."""

        errors: list[str] = []

        def reject(code: str) -> None:
            if code not in errors:
                errors.append(code)

        bounds_valid = (
            len(self.source_bounds) == 6
            and all(isfinite(value) for value in self.source_bounds)
            and all(
                self.source_bounds[index] < self.source_bounds[index + 3]
                for index in range(3)
            )
        )
        if not bounds_valid:
            reject("invalid_source_bounds")

        if len(self.sections) < 2:
            reject("too_few_sections")

        expected_vertex_count = (
            len(self.sections[0])
            if self.sections
            else 0
        )
        for section_index, section in enumerate(self.sections):
            if len(section) < 2:
                reject("zero_length_section_edge")
            if section_index and len(section) != expected_vertex_count:
                reject("inconsistent_section_vertex_count")

            for point in section:
                point_valid = (
                    len(point) == 3
                    and all(isfinite(coordinate) for coordinate in point)
                )
                if not point_valid:
                    reject("nonfinite_point")
                    continue
                if bounds_valid and any(
                    coordinate < self.source_bounds[axis] - _BOUNDS_TOLERANCE
                    or coordinate > self.source_bounds[axis + 3] + _BOUNDS_TOLERANCE
                    for axis, coordinate in enumerate(point)
                ):
                    reject("point_outside_source_bounds")

            if any(
                _points_equal(left, right)
                for left, right in zip(section, section[1:])
            ):
                reject("zero_length_section_edge")

            if (
                section_index
                and len(section) == len(self.sections[section_index - 1])
                and all(
                    _points_equal(left, right)
                    for left, right in zip(
                        self.sections[section_index - 1],
                        section,
                    )
                )
            ):
                reject("repeated_consecutive_sections")

        return tuple(errors)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-native representation of this intermediate value."""

        return {
            "operator": self.operator,
            "sections": [
                [list(point) for point in section]
                for section in self.sections
            ],
            "source_bounds": list(self.source_bounds),
        }


def section_surface_from_bounds(
    bounds: Sequence[float],
    parameters: Mapping[str, Any],
) -> BoundedSurface:
    """Map ordered normalized section controls through live solid bounds."""

    live_bounds = _validated_bounds(bounds)
    span_axis = str(parameters.get("span_axis") or "").lower()
    if span_axis not in {"x", "y"}:
        raise ValueError("section_surface span_axis must be 'x' or 'y'")

    raw_controls = parameters.get("section_controls")
    if (
        not isinstance(raw_controls, Sequence)
        or isinstance(raw_controls, (str, bytes))
        or not 2 <= len(raw_controls) <= 12
    ):
        raise ValueError("section_surface requires 2..12 section_controls")

    controls: list[tuple[float, float]] = []
    for raw_control in raw_controls:
        if (
            not isinstance(raw_control, Sequence)
            or isinstance(raw_control, (str, bytes))
            or len(raw_control) != 2
        ):
            raise ValueError("section_controls must be normalized [u, height] pairs")
        controls.append(
            (
                _normalized_value(raw_control[0], "section control u"),
                _normalized_value(raw_control[1], "section control height"),
            )
        )
    if (
        abs(controls[0][0]) > _POINT_TOLERANCE
        or abs(controls[-1][0] - 1.0) > _POINT_TOLERANCE
        or any(
            left[0] >= right[0]
            for left, right in zip(controls, controls[1:])
        )
    ):
        raise ValueError("section control u values must run from 0 to 1 in order")

    minx, miny, minz, maxx, maxy, maxz = live_bounds
    sections: list[tuple[Vec3, Vec3]] = []
    for position_ratio, height_ratio in controls:
        z = _interpolate(minz, maxz, height_ratio)
        if span_axis == "x":
            x = _interpolate(minx, maxx, position_ratio)
            sections.append(((x, miny, z), (x, maxy, z)))
        else:
            y = _interpolate(miny, maxy, position_ratio)
            sections.append(((minx, y, z), (maxx, y, z)))

    return _validated_surface(
        BoundedSurface("section_surface", tuple(sections), live_bounds)
    )


def loft_surface_from_bounds(
    bounds: Sequence[float],
    parameters: Mapping[str, Any],
) -> BoundedSurface:
    """Map ordered normalized three-dimensional profiles through live bounds."""

    live_bounds = _validated_bounds(bounds)
    raw_profiles = parameters.get("profiles")
    if (
        not isinstance(raw_profiles, Sequence)
        or isinstance(raw_profiles, (str, bytes))
        or not 2 <= len(raw_profiles) <= 12
    ):
        raise ValueError("loft_surface requires 2..12 profiles")

    sections: list[tuple[Vec3, ...]] = []
    for raw_profile in raw_profiles:
        if (
            not isinstance(raw_profile, Sequence)
            or isinstance(raw_profile, (str, bytes))
            or len(raw_profile) < 2
        ):
            raise ValueError("each loft profile requires at least two points")
        sections.append(
            tuple(
                _normalized_point_to_bounds(
                    live_bounds,
                    _normalized_point(raw_point),
                )
                for raw_point in raw_profile
            )
        )

    return _validated_surface(
        BoundedSurface("loft_surface", tuple(sections), live_bounds)
    )


def host_face_surface_from_bounds(
    bounds: Sequence[float],
    parameters: Mapping[str, Any],
) -> BoundedSurface:
    """Return a bounded four-corner sub-surface on a selected live solid face."""

    live_bounds = _validated_bounds(bounds)
    host_face = str(parameters.get("host_face") or "").lower()
    if host_face not in _SUPPORTED_HOST_FACES:
        raise ValueError(f"unsupported host face: {host_face!r}")
    inset_ratio = _normalized_value(
        parameters.get("inset_ratio", 0.0),
        "host face inset_ratio",
    )
    if inset_ratio >= 0.5:
        raise ValueError("host face inset_ratio must be less than 0.5")

    minx, miny, minz, maxx, maxy, maxz = live_bounds
    inset_x = (maxx - minx) * inset_ratio
    inset_y = (maxy - miny) * inset_ratio
    inset_z = (maxz - minz) * inset_ratio
    low_x, high_x = minx + inset_x, maxx - inset_x
    low_y, high_y = miny + inset_y, maxy - inset_y
    low_z, high_z = minz + inset_z, maxz - inset_z

    if host_face in {"top", "bottom"}:
        z = maxz if host_face == "top" else minz
        sections = (
            ((low_x, low_y, z), (low_x, high_y, z)),
            ((high_x, low_y, z), (high_x, high_y, z)),
        )
    elif host_face in {"east", "west"}:
        x = maxx if host_face == "east" else minx
        sections = (
            ((x, low_y, low_z), (x, high_y, low_z)),
            ((x, low_y, high_z), (x, high_y, high_z)),
        )
    else:
        y = maxy if host_face == "north" else miny
        sections = (
            ((low_x, y, low_z), (high_x, y, low_z)),
            ((low_x, y, high_z), (high_x, y, high_z)),
        )

    return _validated_surface(
        BoundedSurface("host_face_surface", sections, live_bounds)
    )


def _validated_bounds(bounds: Sequence[float]) -> Bounds:
    if len(bounds) != 6:
        raise ValueError("live bounds must contain six values")
    values = tuple(float(value) for value in bounds)
    if (
        not all(isfinite(value) for value in values)
        or any(values[index] >= values[index + 3] for index in range(3))
    ):
        raise ValueError("live bounds must be finite positive extents")
    return values


def _normalized_value(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite normalized number") from exc
    if not isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{label} must be within [0, 1]")
    return number


def _normalized_point(point: Any) -> Vec3:
    if (
        not isinstance(point, Sequence)
        or isinstance(point, (str, bytes))
        or len(point) != 3
    ):
        raise ValueError("loft profile points must contain three coordinates")
    return (
        _normalized_value(point[0], "loft point x"),
        _normalized_value(point[1], "loft point y"),
        _normalized_value(point[2], "loft point z"),
    )


def _normalized_point_to_bounds(bounds: Bounds, point: Vec3) -> Vec3:
    return tuple(
        _interpolate(bounds[axis], bounds[axis + 3], point[axis])
        for axis in range(3)
    )


def _validated_surface(surface: BoundedSurface) -> BoundedSurface:
    errors = surface.validate()
    if errors:
        raise ValueError(
            f"invalid {surface.operator}: {', '.join(errors)}"
        )
    return surface


def _interpolate(low: float, high: float, ratio: float) -> float:
    return low + (high - low) * ratio


def _points_equal(left: Vec3, right: Vec3) -> bool:
    return all(
        abs(left_coordinate - right_coordinate) <= _POINT_TOLERANCE
        for left_coordinate, right_coordinate in zip(left, right)
    )
