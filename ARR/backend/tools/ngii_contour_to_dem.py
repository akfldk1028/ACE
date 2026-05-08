"""
NGII 연속수치지형도 SHP → DEM raster (Step 4).

학술 논문 (kibim Rhino Grasshopper) 검증 path. 무료 SHP (data.go.kr/data/15059721)
의 등고선(7111)·표고점(7217) layer를 모아 TIN 보간으로 DEM raster 생성.

Usage:
    cd ARR/backend
    PYTHONIOENCODING=utf-8 python tools/ngii_contour_to_dem.py \\
        D:/Data/NGII_DEM/seoul_contour/ \\
        D:/Data/NGII_DEM/seoul_dem.tif \\
        --resolution 5

생성된 .tif를 .env의 NGII_DEM_LOCAL_PATH 에 지정하고 ELEVATION_PROVIDER=ngii_local_dem
설정하면 elevation_api가 자체 호스팅 DEM 사용.

NGII SHP 좌표계: EPSG:5186 (Korea 2000 / Central Belt 2010).
출력 DEM: EPSG:5186, GeoTIFF, Float32.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from glob import glob
from pathlib import Path


def _setup_stdout():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def collect_z_features(shp_dir: str) -> tuple[list[tuple[float, float, float]], tuple[float, float, float, float]]:
    """SHP 폴더 재귀 스캔. z 값 가진 LineString/Point/MultiLineString 모두에서
    (x, y, z) 점군 추출. 반환: (점군, bbox xmin/ymin/xmax/ymax).
    """
    import geopandas as gpd

    points: list[tuple[float, float, float]] = []
    bbox = [float("inf"), float("inf"), float("-inf"), float("-inf")]
    shp_files = sorted(glob(os.path.join(shp_dir, "**/*.shp"), recursive=True))
    if not shp_files:
        raise FileNotFoundError(f"No .shp files under {shp_dir}")
    print(f"[scan] {len(shp_files)} SHP files in {shp_dir}")

    for shp_path in shp_files:
        try:
            gdf = gpd.read_file(shp_path)
        except Exception as e:
            print(f"  [skip] {os.path.basename(shp_path)}: {e}")
            continue
        n_added_before = len(points)
        for geom in gdf.geometry:
            if geom is None or geom.is_empty or not geom.has_z:
                continue
            t = geom.geom_type
            if t == "Point":
                points.append((geom.x, geom.y, geom.z))
                _update_bbox(bbox, geom.x, geom.y)
            elif t == "MultiPoint":
                for pt in geom.geoms:
                    if pt.has_z:
                        points.append((pt.x, pt.y, pt.z))
                        _update_bbox(bbox, pt.x, pt.y)
            elif t == "LineString":
                for x, y, z in geom.coords:
                    points.append((x, y, z))
                    _update_bbox(bbox, x, y)
            elif t == "MultiLineString":
                for line in geom.geoms:
                    if line.has_z:
                        for x, y, z in line.coords:
                            points.append((x, y, z))
                            _update_bbox(bbox, x, y)
        added = len(points) - n_added_before
        if added > 0:
            print(f"  [+] {os.path.basename(shp_path):50s} +{added:>7,} pts")

    if not points:
        raise ValueError(
            "No z-valued features found. NGII SHP needs LineString z (등고선 7111) "
            "or Point z (표고점 7217)."
        )
    return points, tuple(bbox)


def _update_bbox(bbox: list, x: float, y: float) -> None:
    if x < bbox[0]:
        bbox[0] = x
    if y < bbox[1]:
        bbox[1] = y
    if x > bbox[2]:
        bbox[2] = x
    if y > bbox[3]:
        bbox[3] = y


def build_raster(
    points: list[tuple[float, float, float]],
    bbox: tuple[float, float, float, float],
    resolution_m: float,
    output_tif: str,
    crs: str = "EPSG:5186",
) -> None:
    """Delaunay TIN + LinearNDInterpolator → 격자 raster 보간.

    bbox 외곽은 Delaunay convex hull 내에서만 보간 (외부 NaN → NoData).
    """
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds
    from scipy.interpolate import LinearNDInterpolator

    xmin, ymin, xmax, ymax = bbox
    print(f"[bbox] x={xmin:.1f}~{xmax:.1f} y={ymin:.1f}~{ymax:.1f} "
          f"({(xmax-xmin)/1000:.1f} × {(ymax-ymin)/1000:.1f} km)")
    print(f"[points] {len(points):,} (x, y, z) tuples")

    xy = np.array([(p[0], p[1]) for p in points], dtype=np.float64)
    z = np.array([p[2] for p in points], dtype=np.float64)
    print(f"[interp] building LinearNDInterpolator (TIN)...", flush=True)
    interp = LinearNDInterpolator(xy, z)

    width = max(2, int(math.ceil((xmax - xmin) / resolution_m)))
    height = max(2, int(math.ceil((ymax - ymin) / resolution_m)))
    print(f"[raster] {width}×{height} px @ {resolution_m}m = "
          f"{width*height/1e6:.2f}M cells")

    transform = from_bounds(xmin, ymin, xmax, ymax, width, height)

    # 격자 점 좌표 (셀 중심)
    xs = np.linspace(xmin + resolution_m / 2, xmax - resolution_m / 2, width)
    ys = np.linspace(ymax - resolution_m / 2, ymin + resolution_m / 2, height)
    xx, yy = np.meshgrid(xs, ys)
    print(f"[interp] sampling {width*height:,} cells...", flush=True)
    zz = interp(xx, yy)
    nodata = -9999.0
    zz = np.where(np.isnan(zz), nodata, zz).astype(np.float32)

    Path(os.path.dirname(output_tif) or ".").mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        output_tif, "w",
        driver="GTiff", count=1,
        height=height, width=width,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=nodata,
        compress="DEFLATE",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    ) as dst:
        dst.write(zz, 1)
    size_mb = os.path.getsize(output_tif) / 1024 / 1024
    valid = (zz != nodata).sum()
    print(f"[saved] {output_tif} ({size_mb:.1f}MB, {valid:,}/{width*height:,} valid)")


def main() -> int:
    _setup_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("shp_dir", help="NGII 연속수치지형도 SHP 폴더 (재귀 스캔)")
    ap.add_argument("output_tif", help="출력 GeoTIFF 경로")
    ap.add_argument("--resolution", type=float, default=5.0,
                    help="픽셀 크기 m (기본 5, 1:5,000 권장)")
    ap.add_argument("--crs", default="EPSG:5186",
                    help="입력 SHP 좌표계 (NGII 표준 EPSG:5186)")
    args = ap.parse_args()

    print("=" * 60)
    print("NGII 수치지형도 SHP → DEM raster (Step 4)")
    print("=" * 60)
    points, bbox = collect_z_features(args.shp_dir)
    build_raster(points, bbox, args.resolution, args.output_tif, crs=args.crs)
    print()
    print("다음 단계:")
    print(f"  1. .env 추가: NGII_DEM_LOCAL_PATH={args.output_tif}")
    print(f"  2. .env 변경: ELEVATION_PROVIDER=ngii_local_dem")
    print(f"  3. backend 재시작 후 라이브 검증:")
    print(f"     python tools/verify_datum_multi.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
