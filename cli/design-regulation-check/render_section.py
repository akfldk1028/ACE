#!/usr/bin/env python3
"""Render and verify /design legal datum sections with matplotlib.

This is a frontend-independent QA tool. It calls the same ARR /design APIs as
the VWorld screen, validates datum/envelope basis, and writes PNG section plots.
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


ROOT = Path(__file__).resolve().parent


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
    req = request.Request(
        url,
        data=data,
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout_s) as res:
            body = res.read().decode("utf-8")
            return res.status, json.loads(body)
    except Exception as exc:  # noqa: BLE001 - CLI should report any transport failure.
        return 0, {"error": str(exc)}


def number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def almost_equal(a: Any, b: Any, eps: float = 0.01) -> bool:
    aa = number(a)
    bb = number(b)
    return aa is not None and bb is not None and abs(aa - bb) <= eps


def valid_split_bands(bands: Any) -> bool:
    return (
        isinstance(bands, list)
        and len(bands) > 0
        and all(
            isinstance(band.get("datum_m"), (int, float))
            and isinstance(band.get("length_m"), (int, float))
            and band["length_m"] > 0
            and isinstance(band.get("sample_count"), int)
            and band["sample_count"] > 0
            for band in bands
            if isinstance(band, dict)
        )
    )


def valid_daylight_walls(envelope: dict[str, Any] | None) -> bool:
    walls = envelope.get("walls") if envelope else None
    if not isinstance(walls, list) or not walls:
        return False
    for wall in walls:
        if not isinstance(wall, dict):
            return False
        positions = wall.get("positions")
        mins = wall.get("min_heights")
        maxs = wall.get("max_heights")
        if not isinstance(positions, list) or len(positions) < 2:
            return False
        if not isinstance(mins, list) or not isinstance(maxs, list) or len(mins) != len(maxs):
            return False
        if not all(isinstance(v, (int, float)) for v in mins + maxs):
            return False
        if any(maxs[i] < mins[i] for i in range(len(mins))):
            return False
    return True


def slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value).strip("_")


def validate_case(test_case: dict[str, Any], auto: dict[str, Any]) -> list[str]:
    setbacks = auto.get("setback_geometries") or {}
    datum = setbacks.get("datum_result") or {}
    sunlight = setbacks.get("sunlight_envelope")
    daylight = setbacks.get("daylight_diagonal_envelope")
    checks: list[str] = []

    if datum.get("elevation_source") != "ngii_local_dem":
        checks.append(f"FAIL source={datum.get('elevation_source')}; expected ngii_local_dem")

    if test_case.get("expectSunlight") is True and not sunlight:
        checks.append("FAIL expected sunlight envelope is missing")
    if test_case.get("expectSunlight") is False and sunlight:
        checks.append("FAIL sunlight envelope exists but should be absent")

    if test_case.get("expectDaylight") is not False and not daylight:
        checks.append("FAIL expected daylight diagonal envelope is missing")
    if test_case.get("expectDaylight") is False and daylight:
        checks.append("FAIL daylight diagonal envelope exists but should be absent")

    avg = datum.get("neighbor_avg_datum_m")
    if isinstance(avg, (int, float)) and sunlight:
        if not almost_equal(sunlight.get("datum_elevation_m"), avg):
            checks.append(
                "FAIL sunlight datum "
                f"{sunlight.get('datum_elevation_m')} != neighbor_avg {avg}"
            )
        if sunlight.get("datum_case") != "neighbor_avg_86":
            checks.append(
                "FAIL sunlight datum_case="
                f"{sunlight.get('datum_case')}; expected neighbor_avg_86"
            )

    if daylight and not valid_daylight_walls(daylight):
        checks.append("FAIL daylight wall height structure is invalid")

    if test_case.get("expectSplitBands") and not valid_split_bands(datum.get("split_bands")):
        checks.append("FAIL expected valid split_bands")

    return checks or ["PASS datum/envelope basis checks"]


def render_plot(test_case: dict[str, Any], site: dict[str, Any], auto: dict[str, Any], output: Path) -> dict[str, Any]:
    setbacks = auto.get("setback_geometries") or {}
    datum = setbacks.get("datum_result") or {}
    regs = auto.get("regulations") or {}
    sunlight = setbacks.get("sunlight_envelope")
    daylight = setbacks.get("daylight_diagonal_envelope")
    front_road = setbacks.get("front_road_diagonal_profile") or {}

    parcel = number(datum.get("parcel_datum_m")) or number(datum.get("elevation_m"))
    road = number(datum.get("road_datum_m"))
    neighbor = number(datum.get("neighbor_datum_m"))
    avg86 = number(datum.get("neighbor_avg_datum_m"))
    sunlight_base = number(sunlight.get("datum_elevation_m")) if sunlight else None
    daylight_mult = number(regs.get("daylight_diagonal_multiplier")) or 2.0
    road_width = number(front_road.get("road_width_m")) or 4.0
    road_slope = number(front_road.get("slope")) or 1.5
    road_applies = bool(front_road.get("applies"))

    values = [v for v in [parcel, road, neighbor, avg86, sunlight_base, 0.0, 65.0] if v is not None]
    y_min = min(values) - 3
    y_max = max(values) + 8
    mass_x0 = 6.0
    mass_w = 4.0
    mass_h = 26.0
    mass_color = "#94a3b8"

    fig, axes = plt.subplots(1, 3, figsize=(18, 8.5), dpi=150, sharey=True)
    fig.suptitle(f"{test_case['name']} / {site.get('pnu', test_case['input'])}", x=0.02, ha="left", fontsize=15, fontweight="bold")

    def setup(ax, title: str, xlim: tuple[float, float]) -> None:
        ax.set_facecolor("#ffffff")
        ax.set_xlim(*xlim)
        ax.set_ylim(y_min, y_max)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, color="#e2e8f0", linewidth=0.8)
        ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
        ax.set_xlabel("수평거리 x (m)")
        ax.axhline(0, color="#cbd5e1", linewidth=1)

    def datum_line(ax, label: str, value: float | None, color: str) -> None:
        if value is not None:
            ax.axhline(value, color=color, linestyle="--", linewidth=2, label=f"{label} {value:.2f}m")

    def slope_marker(ax, x0: float, y0: float, ratio: float, color: str, label: str) -> None:
        run = 3.0
        rise = run * ratio
        ax.plot([x0, x0 + run], [y0, y0], color=color, linewidth=1.8)
        ax.plot([x0 + run, x0 + run], [y0, y0 + rise], color=color, linewidth=1.8)
        ax.plot([x0, x0 + run], [y0, y0 + rise], color=color, linewidth=2.2)
        ax.text(x0 + run / 2, y0 - 1.2, "수평 1", ha="center", va="top", color=color, fontsize=8, fontweight="bold")
        ax.text(x0 + run + 0.35, y0 + rise / 2, f"수직 {ratio:g}", ha="left", va="center", color=color, fontsize=8, fontweight="bold")
        ax.text(x0 + run / 2, y0 + rise + 0.8, label, ha="center", va="bottom", color=color, fontsize=8, fontweight="bold")

    def mass(ax, x0: float = mass_x0, base: float | None = None, top: float | None = None) -> float | None:
        if base is None:
            base = parcel
        if base is None:
            return None
        top_v = top if top is not None else base + mass_h
        ax.add_patch(plt.Rectangle((x0, base), mass_w, top_v - base, color=mass_color, alpha=0.65, ec="#475569"))
        ax.text(x0 + mass_w / 2, (base + top_v) / 2, "test mass", ha="center", va="center", fontsize=9, fontweight="bold")
        return top_v

    # 1) 전면도로 사선: opposite road boundary 기준 H = road_datum + 1.5 * distance.
    # Ratio labels use vertical:horizontal, so H=1.5x is 1.5:1.
    ax = axes[0]
    setup(ax, "전면도로 사선 1.5:1 참고 단면", (-road_width - 2, 24))
    ax.set_ylabel("절대 표고 / 법규 기준면 (m)")
    datum_line(ax, "대지 §119", parcel, "#eab308")
    datum_line(ax, "전면도로", road, "#f97316")
    if road is not None:
        ax.fill_between([-road_width, 0], [road, road], [road - 0.4, road - 0.4], color="#fed7aa", alpha=0.8)
        ax.text(-road_width / 2, road - 1.2, f"도로폭 {road_width:.1f}m", ha="center", fontsize=9, color="#9a3412")
        xs = [-road_width, 24]
        ys = [road, road + road_slope * (24 + road_width)]
        ax.plot(xs, ys, color="#f97316", linewidth=3, label=f"전면도로 사선 {road_slope:g}:1 (H={road_slope:g}x)")
        ax.fill_between(xs, ys, road, color="#fed7aa", alpha=0.15)
        slope_marker(ax, -34.0, road + road_slope * 6.0, road_slope, "#f97316", f"{road_slope:g}:1")
    top = mass(ax, x0=6.0)
    if top is not None and road is not None:
        limit = road + road_slope * (6.0 + mass_w + road_width)
        ok = top <= limit + 0.01
        ax.text(0.02, 0.03, f"{'PASS' if ok else 'FAIL'} mass top {top:.1f}m / road limit {limit:.1f}m", transform=ax.transAxes, color="#166534" if ok else "#dc2626", fontsize=9, fontweight="bold")
    if not road_applies:
        ax.text(0.02, 0.92, "현행 도로사선: 삭제/가로구역별 높이제한 대체\n1.5:1은 사용자 기준표 확인용", transform=ax.transAxes, color="#92400e", fontsize=8, va="top")
    ax.legend(loc="upper right", fontsize=8)

    # 2) 정북일조: §86①, H<=10m 1.5m, H>10m H/2.
    # H/2 이격은 단면에서 H = 2x, 즉 vertical:horizontal = 2:1.
    ax = axes[1]
    setup(ax, "정북일조 사선 2:1 (§86①, H=2x)", (0, 24))
    datum_line(ax, "§86 평균수평면", avg86, "#16a34a")
    if sunlight and sunlight_base is not None:
        base_setback = number(sunlight.get("base_setback_m")) or 1.5
        base_height = number(sunlight.get("base_height_m")) or 10.0
        slope = number(sunlight.get("slope")) or 2.0
        plateau_end = number(sunlight.get("plateau_end_m")) or 5.0
        cap_depth = min(number(sunlight.get("max_depth_m")) or 25.0, 24.0)
        xs = [base_setback, base_setback, plateau_end, cap_depth]
        ys = [
            sunlight_base,
            sunlight_base + base_height,
            sunlight_base + base_height,
            sunlight_base + cap_depth * slope,
        ]
        ax.plot(xs[:2], ys[:2], color="#dc2626", linewidth=3)
        ax.plot(xs[1:3], ys[1:3], color="#f472b6", linewidth=3)
        ax.plot(xs[2:], ys[2:], color="#ec4899", linewidth=3, label=f"정북일조 2:1, H0={sunlight_base:.2f}m")
        ax.fill_between([base_setback, plateau_end, cap_depth], [sunlight_base + base_height, sunlight_base + base_height, sunlight_base + cap_depth * slope], sunlight_base, color="#f9a8d4", alpha=0.18)
        slope_marker(ax, 13.0, sunlight_base + 13.0 * slope, 2.0, "#ec4899", "2:1")
    top = mass(ax, x0=6.0)
    if top is not None and sunlight_base is not None:
        x_check = 6.0 + mass_w
        sun_limit = sunlight_base + (10.0 if x_check <= 5.0 else x_check * 2.0)
        ok = top <= sun_limit + 0.01
        ax.text(0.02, 0.03, f"{'PASS' if ok else 'FAIL'} mass top {top:.1f}m / north limit {sun_limit:.1f}m", transform=ax.transAxes, color="#166534" if ok else "#dc2626", fontsize=9, fontweight="bold")
    ax.legend(loc="upper right", fontsize=8)

    # 3) 채광사선: 공동주택 채광창 방향, H <= 경계선 수평거리 × multiplier.
    # multiplier=2 means vertical:horizontal = 2:1.
    ax = axes[2]
    setup(ax, f"채광사선 {daylight_mult:g}:1 (§86③, H={daylight_mult:g}x)", (0, 24))
    datum_line(ax, "대지 §119", parcel, "#eab308")
    datum_line(ax, "인접대지", neighbor, "#2563eb")
    if daylight and parcel is not None:
        xs = [0, 24]
        ys = [parcel, parcel + 24 * daylight_mult]
        ax.plot(xs, ys, color="#7e22ce", linewidth=3, label=f"채광사선 {daylight_mult:g}:1, parcel H0={parcel:.2f}m")
        ax.fill_between(xs, ys, parcel, color="#c084fc", alpha=0.16)
        slope_marker(ax, 13.0, parcel + 13.0 * daylight_mult, daylight_mult, "#7e22ce", f"{daylight_mult:g}:1")
    top = mass(ax, x0=6.0)
    if top is not None and parcel is not None:
        x_check = 6.0 + mass_w
        daylight_limit = parcel + x_check * daylight_mult
        ok = top <= daylight_limit + 0.01
        ax.text(0.02, 0.03, f"{'PASS' if ok else 'FAIL'} mass top {top:.1f}m / daylight limit {daylight_limit:.1f}m", transform=ax.transAxes, color="#166534" if ok else "#dc2626", fontsize=9, fontweight="bold")
    ax.legend(loc="upper right", fontsize=8)

    checks = validate_case(test_case, auto)
    y_text = 0.01
    for check in checks:
        color = "#dc2626" if check.startswith("FAIL") else "#166534"
        fig.text(0.02, y_text, check, color=color, fontsize=9, fontweight="bold")
        y_text += 0.025

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(output)
    plt.close(fig)

    return {
        "name": test_case["name"],
        "file": str(output),
        "pass": all(not c.startswith("FAIL") for c in checks),
        "checks": checks,
        "pnu": site.get("pnu", test_case["input"]),
        "parcelDatum": parcel,
        "roadDatum": road,
        "neighborDatum": neighbor,
        "neighborAvgDatum": avg86,
        "sunlightDatum": sunlight_base,
        "sunlightCase": sunlight.get("datum_case") if sunlight else None,
        "daylightWalls": len(daylight.get("walls") or []) if daylight else 0,
        "source": datum.get("elevation_source"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--cases", default=str(ROOT / "cases.json"))
    parser.add_argument("--out-dir", default=str(ROOT / "out" / "pysections"))
    parser.add_argument("--timeout", type=float, default=240.0)
    args = parser.parse_args()

    base = args.base.rstrip("/")
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    outputs: list[dict[str, Any]] = []

    for test_case in cases:
        site_status, site = post_json(f"{base}/design/site-boundary/", {"pnu": test_case["input"]}, args.timeout)
        if site_status != 200 or not site.get("geometry"):
            outputs.append({"name": test_case["name"], "pass": False, "error": site.get("error") or f"site status {site_status}"})
            continue
        auto_status, auto = post_json(
            f"{base}/design/auto-constraints/",
            {
                "pnu": site.get("pnu", test_case["input"]),
                "site_polygon": site["geometry"],
                "building_type": test_case.get("buildingType", "공동주택"),
            },
            args.timeout,
        )
        if auto_status != 200 or auto.get("error"):
            outputs.append({"name": test_case["name"], "pass": False, "error": auto.get("error") or f"auto status {auto_status}"})
            continue
        output = out_dir / f"{slug(test_case['name'])}.png"
        outputs.append(render_plot(test_case, site, auto, output))

    summary = {
        "baseUrl": base,
        "pass": all(item.get("pass") for item in outputs),
        "outputs": outputs,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
