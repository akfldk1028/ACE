"""Collect a deterministic, read-only ARR candidate source for site selection."""

from __future__ import annotations

import argparse
import logging
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from iclr2027.candidate_source import (
    BoundingBox,
    CandidateObservation,
    CoordinateProbe,
    ExclusionCode,
    MAX_PROBES,
    ProbeExclusion,
    collect_candidate_source,
)
from iclr2027.io import write_json_atomic


SEOUL_BBOX = BoundingBox(
    west=126.7644,
    south=37.4133,
    east=127.1839,
    north=37.7151,
)
DEFAULT_SEED = 20260818
DEFAULT_MAX_PROBES = 256
NOMINAL_PARKING_FACILITY_AREA_M2 = 1000.0
REQUIRED_PROGRAM_SLUGS = ("neighborhood", "gymnasium", "cultural")
_PNU = re.compile(r"^[0-9]{19}$")


@dataclass(frozen=True)
class ArrDependencies:
    """Injected ARR read/calculation boundaries used for one coordinate probe."""

    reverse_geocode: Callable[[float, float], Mapping[str, Any]]
    fetch_land_use_attr: Callable[[str], Mapping[str, Any]]
    fetch_ladfrl: Callable[[str], Mapping[str, Any]]
    zone_lookup: Callable[[str], Mapping[str, Any] | None]
    calculate_all: Callable[..., Mapping[str, Any]]
    resolve_parking: Callable[..., Mapping[str, Any]]
    parking_rules: Mapping[str, Any]
    programs: tuple[Any, ...]


def configure_collection_logging() -> None:
    """Keep HTTP request URLs and query strings out of normal collection logs."""

    logging.getLogger("httpx").setLevel(logging.WARNING)


def _positive_finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _has_boundary(geometry: Any) -> bool:
    if not isinstance(geometry, Mapping):
        return False
    return (
        geometry.get("type") in {"Polygon", "MultiPolygon"}
        and isinstance(geometry.get("coordinates"), list)
        and bool(geometry["coordinates"])
    )


def inspect_arr_probe(
    probe: CoordinateProbe,
    dependencies: ArrDependencies,
) -> CandidateObservation | ProbeExclusion:
    """Inspect one point using only ARR's live reads and deterministic rules."""

    reverse = dependencies.reverse_geocode(probe.longitude, probe.latitude)
    if reverse.get("success") is not True or not reverse.get("pnu"):
        return ProbeExclusion(ExclusionCode.NO_PARCEL)

    pnu = str(reverse.get("pnu"))
    if not _PNU.fullmatch(pnu):
        return ProbeExclusion(ExclusionCode.INVALID_PNU)
    if not pnu.startswith("11"):
        return ProbeExclusion(ExclusionCode.OUTSIDE_SEOUL, pnu)

    land_use = dependencies.fetch_land_use_attr(pnu)
    cadastre = dependencies.fetch_ladfrl(pnu)
    area = _positive_finite(cadastre.get("land_area_m2"))
    if cadastre.get("success") is not True or area is None:
        return ProbeExclusion(ExclusionCode.PARCEL_AREA_UNAVAILABLE, pnu)

    zones = [
        str(zone)
        for zone in land_use.get("zones", [])
        if isinstance(zone, str) and zone.strip()
    ]
    mapped_zones = [zone for zone in zones if dependencies.zone_lookup(zone) is not None]
    regulations = dependencies.calculate_all(
        zones,
        land_info={"land_area_m2": area},
        sigungu_code=pnu[:5],
        use_llm_extraction=False,
    )
    matched_zones = regulations.get("matched_zones")
    bcr = _positive_finite(regulations.get("bcr_pct"))
    far = _positive_finite(regulations.get("far_pct"))
    law_available = (
        land_use.get("success") is True
        and bool(mapped_zones)
        and isinstance(matched_zones, list)
        and bool(matched_zones)
        and bcr is not None
        and far is not None
    )

    programs_by_slug = {
        str(program.slug): program
        for program in dependencies.programs
        if getattr(program, "slug", None)
    }
    parking_available = all(
        slug in programs_by_slug for slug in REQUIRED_PROGRAM_SLUGS
    )
    for slug in REQUIRED_PROGRAM_SLUGS:
        program = programs_by_slug.get(slug)
        if program is None:
            continue
        result = dependencies.resolve_parking(
            pnu=pnu,
            building_type=str(program.building_type),
            facility_area_m2=NOMINAL_PARKING_FACILITY_AREA_M2,
            rules=dict(dependencies.parking_rules),
            rules_provenance={
                "source": "local_structured_seed",
                "graph_status": "not_requested",
            },
        )
        required_spaces = result.get("required_spaces")
        if type(required_spaces) is not int or required_spaces < 0:
            parking_available = False

    return CandidateObservation(
        pnu=pnu,
        district_code=pnu[:5],
        parcel_area_m2=area,
        boundary_available=_has_boundary(reverse.get("geometry")),
        law_available=law_available,
        parking_available=parking_available,
    )


def _default_arr_backend() -> Path:
    return Path(__file__).resolve().parents[2] / "ARR" / "backend"


def _load_backend_environment(arr_backend: Path) -> bool:
    """Load ARR's local environment without replacing process-level values."""

    from dotenv import load_dotenv

    return bool(load_dotenv(dotenv_path=arr_backend / ".env", override=False))


def _load_arr_dependencies(arr_backend: Path) -> ArrDependencies:
    backend = arr_backend.resolve()
    if not backend.is_dir():
        raise RuntimeError(f"ARR backend directory does not exist: {backend}")
    backend_text = str(backend)
    if backend_text not in sys.path:
        sys.path.insert(0, backend_text)
    _load_backend_environment(backend)

    from design.maas.book_language.program_catalog import PROGRAMS
    from design.maas.parking_requirements import (
        _load_structured_seed_rules,
        resolve_candidate_parking_requirement,
    )
    from land import config
    from land.services import land_api, regulation_calculator, zoning_mapper
    from land.services.pnu_resolver import reverse_geocode

    if not config.VWORLD_API_KEY:
        raise RuntimeError("VWORLD_API_KEY is not configured")
    parking_rules = _load_structured_seed_rules()
    if not isinstance(parking_rules, dict) or not parking_rules.get("national"):
        raise RuntimeError("ARR local structured parking rules are unavailable")

    return ArrDependencies(
        reverse_geocode=reverse_geocode,
        fetch_land_use_attr=land_api._fetch_land_use_attr,
        fetch_ladfrl=land_api._fetch_ladfrl,
        zone_lookup=zoning_mapper.lookup,
        calculate_all=regulation_calculator.calculate_all,
        resolve_parking=resolve_candidate_parking_requirement,
        parking_rules=parking_rules,
        programs=tuple(PROGRAMS),
    )


def _bounded_probe_count(value: str) -> int:
    try:
        count = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("max probes must be an integer") from exc
    if not 1 <= count <= MAX_PROBES:
        raise argparse.ArgumentTypeError(
            f"max probes must be between 1 and {MAX_PROBES}"
        )
    return count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--max-probes",
        type=_bounded_probe_count,
        default=DEFAULT_MAX_PROBES,
    )
    parser.add_argument("--west", type=float, default=SEOUL_BBOX.west)
    parser.add_argument("--south", type=float, default=SEOUL_BBOX.south)
    parser.add_argument("--east", type=float, default=SEOUL_BBOX.east)
    parser.add_argument("--north", type=float, default=SEOUL_BBOX.north)
    parser.add_argument("--arr-backend", type=Path, default=_default_arr_backend())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/iclr2027/candidate_source.json"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_collection_logging()
    dependencies = _load_arr_dependencies(args.arr_backend)
    bbox = BoundingBox(
        west=args.west,
        south=args.south,
        east=args.east,
        north=args.north,
    )
    payload = collect_candidate_source(
        bbox=bbox,
        seed=args.seed,
        max_probes=args.max_probes,
        inspect_probe=lambda probe: inspect_arr_probe(probe, dependencies),
        collector="arr-vworld-static-law-local-parking-v1",
        provenance={
            "reverse_geocode_source": "ARR Vworld cadastral point lookup (no cache)",
            "land_read_source": "ARR Vworld private read-only land helpers (no cache)",
            "law_source": "ARR zoning mapper and deterministic regulation calculator",
            "llm_extraction_enabled": False,
            "parking_rule_source": "ARR local structured parking rules",
            "parking_nominal_facility_area_m2": NOMINAL_PARKING_FACILITY_AREA_M2,
            "parking_programs": [str(program.slug) for program in dependencies.programs],
        },
    )
    write_json_atomic(args.output, payload)
    print(
        f"collected {len(payload['candidates'])} unique candidates "
        f"from {payload['provenance']['probes_attempted']} probes into {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
