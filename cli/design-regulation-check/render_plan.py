#!/usr/bin/env python3
"""Render /design plan-view datum QA PNGs.

This complements render_section.py. It verifies where parcel, road, and
neighbor datum values belong in plan view before the same data is trusted in
VWorld/Cesium.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib import request

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from pyproj import Transformer  # noqa: E402
from shapely.geometry import GeometryCollection, LineString, MultiLineString, MultiPolygon, Point, Polygon, shape  # noqa: E402
from shapely.ops import transform  # noqa: E402


ROOT = Path(__file__).resolve().parent
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32652", always_xy=True)


def configure_korean_font() -> None:
    candidates = [
        Path.home() / ".fonts" / "NotoSansKR-Regular.ttf",
        Path.home() / ".fonts" / "NanumGothic-Regular.ttf",
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    ]
    for font_path in candidates:
        if font_path.exists():
            font_manager.fontManager.addfont(str(font_path))
            family = font_manager.FontProperties(fname=str(font_path)).get_name()
            plt.rcParams["font.family"] = family
            plt.rcParams["axes.unicode_minus"] = False
            return


configure_korean_font()


def post_json(url: str, payload: dict[str, Any], timeout_s: float) -> tuple[int, dict[str, Any]]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url, data=data, headers={"content-type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=timeout_s) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return 0, {"error": str(exc)}


def slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value).strip("_")


def number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def to_utm(geojson: dict[str, Any] | None):
    if not geojson:
        return None
    try:
        return transform(TO_UTM.transform, shape(geojson))
    except Exception:
        return None


def edge_to_utm(edge: Any):
    if not isinstance(edge, list) or len(edge) < 2:
        return None
    try:
        return transform(TO_UTM.transform, LineString(edge))
    except Exception:
        return None


def point_to_utm(lng: Any, lat: Any):
    if not isinstance(lng, (int, float)) or not isinstance(lat, (int, float)):
        return None
    try:
        x, y = TO_UTM.transform(float(lng), float(lat))
        return x, y
    except Exception:
        return None


def shifted_xy(geom, origin: tuple[float, float]):
    if geom is None:
        return [], []
    if isinstance(geom, Polygon):
        xs, ys = geom.exterior.xy
        return [x - origin[0] for x in xs], [y - origin[1] for y in ys]
    if isinstance(geom, LineString):
        xs, ys = geom.xy
        return [x - origin[0] for x in xs], [y - origin[1] for y in ys]
    return [], []


def iter_polygons(geom):
    if isinstance(geom, Polygon):
        yield geom
    elif isinstance(geom, MultiPolygon):
        yield from geom.geoms
    elif isinstance(geom, GeometryCollection):
        for part in geom.geoms:
            yield from iter_polygons(part)


def iter_lines(geom):
    if isinstance(geom, LineString):
        yield geom
    elif isinstance(geom, MultiLineString):
        yield from geom.geoms
    elif isinstance(geom, GeometryCollection):
        for part in geom.geoms:
            yield from iter_lines(part)


def label_at(ax, geom, origin: tuple[float, float], text: str, color: str, dx: float = 0.0, dy: float = 0.0) -> None:
    if geom is None or geom.is_empty:
        return
    point = geom.interpolate(0.5, normalized=True) if isinstance(geom, LineString) else geom.representative_point()
    ax.text(point.x - origin[0] + dx, point.y - origin[1] + dy, text, color=color, fontsize=9, fontweight="bold",
            bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": color, "alpha": 0.82})


def add_callout(ax, items: list[str], title: str, loc: tuple[float, float] = (1.02, 0.98)) -> None:
    ax.text(
        loc[0],
        loc[1],
        title + "\n" + "\n".join(items),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        bbox={"boxstyle": "round,pad=0.45", "fc": "white", "ec": "#334155", "alpha": 0.95},
    )


def weighted_sample_point(samples: Any, lng_key: str, lat_key: str, weight_key: str | None = None) -> tuple[float, float] | None:
    if not isinstance(samples, list) or not samples:
        return None
    sx = sy = sw = 0.0
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        pt = point_to_utm(sample.get(lng_key), sample.get(lat_key))
        if pt is None:
            continue
        weight = number(sample.get(weight_key)) if weight_key else None
        if weight is None or weight <= 0:
            weight = 1.0
        sx += pt[0] * weight
        sy += pt[1] * weight
        sw += weight
    if sw <= 0:
        return None
    return sx / sw, sy / sw


def datum_marker(ax, xy: tuple[float, float] | None, origin: tuple[float, float], text: str, color: str, marker: str = "D") -> None:
    if xy is None:
        return
    x = xy[0] - origin[0]
    y = xy[1] - origin[1]
    ax.scatter([x], [y], s=90, marker=marker, color=color, edgecolors="white", linewidths=1.2, zorder=10)
    ax.annotate(
        text,
        xy=(x, y),
        xytext=(x + 4.0, y + 4.0),
        textcoords="data",
        color=color,
        fontsize=8.5,
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": color, "lw": 1.1},
        bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": color, "alpha": 0.9},
        zorder=11,
    )


def line_midpoint_xy(line: LineString | None) -> tuple[float, float] | None:
    if line is None or line.is_empty:
        return None
    point = line.interpolate(0.5, normalized=True)
    return point.x, point.y


def northern_shared_edge(neighbor_parcels: Any, site_geom) -> LineString | None:
    edges: list[LineString] = []
    if not isinstance(neighbor_parcels, list):
        return None
    for neighbor in neighbor_parcels:
        if not isinstance(neighbor, dict):
            continue
        edge = edge_to_utm(neighbor.get("sharedEdge") or neighbor.get("shared_edge"))
        if edge is not None and edge.distance(site_geom.boundary) <= 2.0:
            edges.append(edge)
    if not edges:
        return None
    return max(edges, key=lambda e: e.interpolate(0.5, normalized=True).y)


def draw_geojson(ax, geojson: dict[str, Any] | None, origin: tuple[float, float], color: str, label: str,
                 linewidth: float = 2.0, alpha: float = 1.0, fill: bool = False) -> int:
    geom = to_utm(geojson)
    if geom is None:
        return 0
    count = 0
    for poly in iter_polygons(geom):
        xs, ys = shifted_xy(poly, origin)
        if fill:
            ax.fill(xs, ys, color=color, alpha=alpha, label=label if count == 0 else None)
        ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha, label=None if fill or count else label)
        count += 1
    for line in iter_lines(geom):
        xs, ys = shifted_xy(line, origin)
        ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha, label=label if count == 0 else None)
        count += 1
    return count


def draw_plan(test_case: dict[str, Any], site: dict[str, Any], auto: dict[str, Any], output: Path) -> dict[str, Any]:
    site_geom = to_utm(site.get("geometry"))
    if site_geom is None:
        raise ValueError("site geometry missing")
    origin_pt = site_geom.centroid
    origin = (origin_pt.x, origin_pt.y)

    sg = auto.get("setback_geometries") or {}
    datum = sg.get("datum_result") or {}
    parcel = number(datum.get("parcel_datum_m") or datum.get("elevation_m"))
    road = number(datum.get("road_datum_m"))
    neighbor = number(datum.get("neighbor_datum_m"))
    avg86 = number(datum.get("neighbor_avg_datum_m"))
    checks: list[str] = []

    fig, ax = plt.subplots(figsize=(12, 9), dpi=160)
    ax.set_title(f"{test_case['name']} 평면 레벨 검증 / {site.get('pnu', test_case['input'])}", loc="left", fontsize=13, fontweight="bold")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, color="#e2e8f0", linewidth=0.8)
    ax.set_xlabel("동서 상대거리 (m)")
    ax.set_ylabel("남북 상대거리 (m)")

    for poly in iter_polygons(site_geom):
        xs, ys = shifted_xy(poly, origin)
        ax.fill(xs, ys, color="#fde68a", alpha=0.34, label="대지")
        ax.plot(xs, ys, color="#ca8a04", linewidth=3.0, zorder=4)

    def geometry_context_check(name: str, geojson: dict[str, Any] | None, max_distance_m: float) -> None:
        geom = to_utm(geojson)
        if geom is None or geom.is_empty:
            return
        distance = geom.distance(site_geom)
        if distance > max_distance_m:
            checks.append(f"FAIL {name} geometry is {distance:.1f}m from site; expected <= {max_distance_m:.1f}m")

    geometry_context_check("buildable_area", sg.get("buildable_area", {}).get("geometry"), 1.0)
    geometry_context_check("adjacent_setback", sg.get("adjacent_setback", {}).get("geometry"), 5.0)
    geometry_context_check("north_setback", sg.get("north_setback", {}).get("geometry"), 5.0)
    geometry_context_check("road_setback", sg.get("road_setback", {}).get("geometry"), 8.0)

    # Cadastral context first: neighboring parcels and road parcels.
    neighbor_count = 0
    neighbor_label_added = False
    for neighbor_parcel in sg.get("neighbor_parcels") or []:
        geom = to_utm(neighbor_parcel.get("geometry"))
        if geom is not None:
            distance = geom.distance(site_geom)
            if distance > 2.0:
                checks.append(f"FAIL neighbor parcel geometry is {distance:.1f}m from site")
            for poly in iter_polygons(geom):
                xs, ys = shifted_xy(poly, origin)
                ax.fill(xs, ys, color="#dbeafe", alpha=0.28, label="인접 필지" if not neighbor_label_added else None, zorder=0)
                ax.plot(xs, ys, color="#2563eb", linewidth=1.3, alpha=0.75, zorder=1)
                neighbor_label_added = True
                neighbor_count += 1

    road_count = 0
    road_poly_label_added = False
    for frontage in sg.get("road_frontages") or []:
        road_geom = to_utm(frontage.get("geometry"))
        if road_geom is not None:
            for poly in iter_polygons(road_geom):
                xs, ys = shifted_xy(poly, origin)
                ax.fill(xs, ys, color="#fed7aa", alpha=0.3, label="도로 필지" if not road_poly_label_added else None, zorder=0)
                ax.plot(xs, ys, color="#ea580c", linewidth=1.2, alpha=0.8, zorder=1)
                road_poly_label_added = True

    draw_geojson(ax, sg.get("buildable_area", {}).get("geometry"), origin, "#22c55e", "건축가능영역", linewidth=1.2, alpha=0.16, fill=True)
    draw_geojson(ax, sg.get("adjacent_setback", {}).get("geometry"), origin, "#2563eb", "인접대지 이격선", linewidth=2.0)
    draw_geojson(ax, sg.get("north_setback", {}).get("geometry"), origin, "#ec4899", "정북 이격선", linewidth=2.0)
    draw_geojson(ax, sg.get("road_setback", {}).get("geometry"), origin, "#f97316", "도로/건축선 후퇴", linewidth=2.0)

    road_label_items: list[str] = []
    for frontage in sg.get("road_frontages") or []:
        edge = edge_to_utm(frontage.get("sharedEdge"))
        if edge is None:
            continue
        distance = edge.distance(site_geom.boundary)
        if distance > 2.0:
            checks.append(f"FAIL road frontage edge is {distance:.1f}m from site boundary")
        xs, ys = shifted_xy(edge, origin)
        width = number(frontage.get("roadWidthM"))
        ax.plot(xs, ys, color="#ea580c", linewidth=3.5, label="도로 접면" if road_count == 0 else None, zorder=5)
        label = f"도로레벨 {road:.2f}m" if road is not None else "도로레벨 missing"
        if width is not None:
            label += f" / 폭 {width:.1f}m"
        road_label_items.append(label)
        road_count += 1

    parcel_segments = datum.get("parcel_segments") or []
    if isinstance(parcel_segments, list):
        for idx, seg in enumerate(parcel_segments[:80]):
            pt = point_to_utm(seg.get("midpoint_lng"), seg.get("midpoint_lat")) if isinstance(seg, dict) else None
            if pt is None:
                continue
            x, y = pt[0] - origin[0], pt[1] - origin[1]
            if site_geom.boundary.distance(Point(pt[0], pt[1])) > 5.0:
                checks.append("FAIL parcel sample is not on/near site boundary")
            ax.scatter([x], [y], s=20, color="#ca8a04", edgecolors="white", linewidths=0.7, zorder=6,
                       label="대지 표고 샘플" if idx == 0 else None)
            if idx < 8:
                elev = seg.get("midpoint_elev_m")
                length = seg.get("length_m")
                ax.text(x + 0.5, y + 0.5, f"{elev:.1f}" if isinstance(elev, (int, float)) and isinstance(length, (int, float)) else "s",
                        color="#854d0e", fontsize=6.5)

    road_samples = datum.get("road_samples") or []
    if isinstance(road_samples, list):
        for idx, sample in enumerate(road_samples[:80]):
            pt = point_to_utm(sample.get("lng"), sample.get("lat")) if isinstance(sample, dict) else None
            if pt is None:
                continue
            x, y = pt[0] - origin[0], pt[1] - origin[1]
            ax.scatter([x], [y], s=28, marker="s", color="#ea580c", edgecolors="white", linewidths=0.8, zorder=7,
                       label="도로 표고 샘플" if idx == 0 else None)
            if idx < 8:
                elev = sample.get("elev_m")
                dist = sample.get("dist_m")
                ax.text(x + 0.5, y - 1.0, f"{elev:.1f}" if isinstance(elev, (int, float)) and isinstance(dist, (int, float)) else "r",
                        color="#9a3412", fontsize=6.5)

    neighbor_segments = datum.get("neighbor_segments") or []
    if isinstance(neighbor_segments, list):
        for idx, seg in enumerate(neighbor_segments[:80]):
            pt = point_to_utm(seg.get("midpoint_lng"), seg.get("midpoint_lat")) if isinstance(seg, dict) else None
            if pt is None:
                continue
            x, y = pt[0] - origin[0], pt[1] - origin[1]
            ax.scatter([x], [y], s=18, color="#2563eb", edgecolors="white", linewidths=0.7, zorder=6,
                       label="인접대지 표고 샘플" if idx == 0 else None)
            if idx < 8:
                elev = seg.get("midpoint_elev_m")
                ax.text(x + 0.5, y + 0.5, f"{elev:.1f}" if isinstance(elev, (int, float)) else "n",
                        color="#1d4ed8", fontsize=6.5)

    neighbor_label_items: list[str] = []
    selected_neighbor_edge = northern_shared_edge(sg.get("neighbor_parcels"), site_geom)
    for neighbor_parcel in sg.get("neighbor_parcels") or []:
        edge = edge_to_utm(neighbor_parcel.get("sharedEdge"))
        if edge is not None:
            distance = edge.distance(site_geom.boundary)
            if distance > 2.0:
                checks.append(f"FAIL neighbor shared edge is {distance:.1f}m from site boundary")
            xs, ys = shifted_xy(edge, origin)
            ax.plot(xs, ys, color="#1d4ed8", linewidth=3, zorder=5)
            label = f"인접대지레벨 {neighbor:.2f}m" if neighbor is not None else "인접대지레벨 missing"
            if avg86 is not None:
                label += f" / §86 평균 {avg86:.2f}m"
            neighbor_label_items.append(label)

    parcel_basis = weighted_sample_point(parcel_segments, "midpoint_lng", "midpoint_lat", "length_m")
    road_basis = weighted_sample_point(road_samples, "lng", "lat", None)
    neighbor_basis = weighted_sample_point(neighbor_segments, "midpoint_lng", "midpoint_lat", "length_m")
    neighbor_display_basis = line_midpoint_xy(selected_neighbor_edge) or neighbor_basis
    datum_marker(ax, parcel_basis or (site_geom.centroid.x, site_geom.centroid.y), origin,
                 f"대지 §119\n{parcel:.2f}m" if parcel is not None else "대지 §119\nmissing", "#ca8a04", "D")
    datum_marker(ax, road_basis, origin,
                 f"도로레벨\n{road:.2f}m" if road is not None else "도로레벨\nmissing", "#ea580c", "s")
    datum_marker(ax, neighbor_display_basis, origin,
                 f"인접대지레벨\n{neighbor:.2f}m" if neighbor is not None else "인접대지레벨\nmissing", "#2563eb", "o")
    if parcel_basis is not None and neighbor_display_basis is not None and avg86 is not None:
        avg_xy = ((parcel_basis[0] + neighbor_display_basis[0]) / 2.0, (parcel_basis[1] + neighbor_display_basis[1]) / 2.0)
        datum_marker(ax, avg_xy, origin, f"§86 평균\n{avg86:.2f}m", "#ec4899", "X")

    if road_count == 0:
        ax.text(0.02, 0.96, "WARN: road_frontages 없음 - 도로레벨 위치 검증 약함", transform=ax.transAxes,
                color="#b45309", fontsize=9, fontweight="bold", va="top")
    if neighbor_count == 0:
        ax.text(0.02, 0.91, "WARN: neighbor_parcels 없음 - 인접대지 위치 검증 약함", transform=ax.transAxes,
                color="#1d4ed8", fontsize=9, fontweight="bold", va="top")
    if not parcel_segments:
        ax.text(0.02, 0.86, "WARN: parcel_segments 없음 - 대지 가중평균 샘플 위치 검증 불가", transform=ax.transAxes,
                color="#854d0e", fontsize=9, fontweight="bold", va="top")
    if road is not None and not road_samples:
        ax.text(0.02, 0.81, "WARN: road_samples 없음 - 도로 가중평균 샘플 위치 검증 불가", transform=ax.transAxes,
                color="#9a3412", fontsize=9, fontweight="bold", va="top")

    add_callout(
        ax,
        [
            f"source: {datum.get('elevation_source')}",
            f"대지 §119: {parcel:.2f}m" if parcel is not None else "대지 §119: missing",
            f"도로: {road:.2f}m" if road is not None else "도로: missing",
            f"인접대지: {neighbor:.2f}m" if neighbor is not None else "인접대지: missing",
            f"§86 평균: {avg86:.2f}m" if avg86 is not None else "§86 평균: missing",
            f"대지 샘플: {len(parcel_segments) if isinstance(parcel_segments, list) else 0}",
            f"도로 샘플: {len(road_samples) if isinstance(road_samples, list) else 0}",
            f"인접 샘플: {len(neighbor_segments) if isinstance(neighbor_segments, list) else 0}",
        ],
        "레벨 요약",
        (1.02, 0.98),
    )
    add_callout(
        ax,
        (road_label_items[:4] or ["도로 접면 없음"]) + (neighbor_label_items[:4] or ["인접대지 접면 없음"]),
        "접면 요약",
        (1.02, 0.55),
    )
    ax.legend(loc="upper right", fontsize=8)
    minx, miny, maxx, maxy = site_geom.bounds
    width = maxx - minx
    height = maxy - miny
    margin = max(15.0, min(60.0, max(width, height) * 0.2))
    ax.set_xlim(minx - origin[0] - margin, maxx - origin[0] + margin)
    ax.set_ylim(miny - origin[1] - margin, maxy - origin[1] + margin)
    fig.subplots_adjust(right=0.76)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)

    if datum.get("elevation_source") != "ngii_local_dem":
        checks.append(f"FAIL source={datum.get('elevation_source')}; expected ngii_local_dem")
    if road is None:
        checks.append("FAIL road datum missing")
    if neighbor is None:
        checks.append("FAIL neighbor datum missing")
    if not checks and (road_count == 0 or neighbor_count == 0):
        checks.append("WARN geometry context incomplete")
    if not checks and not parcel_segments:
        checks.append("FAIL parcel weighted-average samples missing")
    return {
        "name": test_case["name"],
        "file": str(output),
        "checks": checks or ["PASS plan datum geometry checks"],
        "pnu": site.get("pnu"),
        "parcelDatum": parcel,
        "roadDatum": road,
        "neighborDatum": neighbor,
        "neighborAvgDatum": avg86,
        "roadFrontages": road_count,
        "neighborParcels": neighbor_count,
        "parcelSamples": len(parcel_segments) if isinstance(parcel_segments, list) else 0,
        "roadSamples": len(road_samples) if isinstance(road_samples, list) else 0,
        "neighborSamples": len(neighbor_segments) if isinstance(neighbor_segments, list) else 0,
        "source": datum.get("elevation_source"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--cases", default=str(ROOT / "cases.json"))
    parser.add_argument("--out-dir", default=str(ROOT / "out" / "plan"))
    parser.add_argument("--timeout", type=float, default=240.0)
    args = parser.parse_args()

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    outputs = []
    failed = False
    for test_case in cases:
        site_status, site = post_json(f"{args.base}/design/site-boundary/", {"pnu": test_case["input"]}, args.timeout)
        if site_status != 200:
            outputs.append({"name": test_case["name"], "pass": False, "error": site})
            failed = True
            continue
        auto_status, auto = post_json(
            f"{args.base}/design/auto-constraints/",
            {
                "pnu": site.get("pnu", test_case["input"]),
                "site_polygon": site.get("geometry"),
                "building_type": test_case.get("buildingType", "공동주택"),
            },
            args.timeout,
        )
        if auto_status != 200:
            outputs.append({"name": test_case["name"], "pass": False, "error": auto})
            failed = True
            continue
        result = draw_plan(test_case, site, auto, out_dir / f"{slug(test_case['name'])}.png")
        result["pass"] = not any(str(c).startswith("FAIL") for c in result["checks"])
        outputs.append(result)
        failed = failed or not result["pass"]

    summary = {"baseUrl": args.base, "pass": not failed, "outputs": outputs}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
