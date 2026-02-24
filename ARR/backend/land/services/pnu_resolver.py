"""
PNU Resolver - validates/parses 19-digit PNU codes and resolves addresses via Vworld API.

PNU structure (19 digits):
  [시도2][시군구3][읍면동3][리2][토지구분1][본번4][부번4] 토지구분: 1=대, 2=임야

Vworld Geocoding:
  1) 주소 → 좌표 (api.vworld.kr/req/address)
  2) 좌표 → 지번주소 (api.vworld.kr/req/address reverse)
  Requires VWORLD_API_KEY env var (https://www.vworld.kr 에서 발급)
"""

import logging
import os
import re

import httpx

logger = logging.getLogger(__name__)

_PNU_PATTERN = re.compile(r"^\d{19}$")
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

VWORLD_API_KEY = os.getenv("VWORLD_API_KEY", "")
VWORLD_GEOCODE_URL = "https://api.vworld.kr/req/address"


def validate_pnu(pnu: str) -> bool:
    """Check if a string is a valid 19-digit PNU code."""
    return bool(_PNU_PATTERN.match(pnu))


def parse_pnu(pnu: str) -> dict | None:
    """
    Parse a 19-digit PNU into components.

    Returns None if invalid, otherwise:
    {
        "pnu": str,
        "sido": str (2),
        "sigungu": str (3),
        "eupmyeondong": str (3),
        "ri": str (2),
        "land_type": str (1) - "1"=대, "2"=임야,
        "main_number": str (4),
        "sub_number": str (4)
    }
    """
    if not validate_pnu(pnu):
        return None

    return {
        "pnu": pnu,
        "sido": pnu[0:2],
        "sigungu": pnu[2:5],
        "eupmyeondong": pnu[5:8],
        "ri": pnu[8:10],
        "land_type": pnu[10:11],
        "main_number": pnu[11:15],
        "sub_number": pnu[15:19],
        "land_type_name": "대" if pnu[10] == "1" else "임야" if pnu[10] == "2" else "기타",
    }


def resolve_address(address: str) -> dict:
    """
    Resolve a Korean address to PNU via Vworld Geocoding API.

    Flow: 주소 → Vworld geocode → 좌표 + 법정동코드 + 지번

    Requires VWORLD_API_KEY env var.

    Returns:
        {
            "success": bool,
            "address": str,
            "pnu": str | None,
            "coordinates": {"x": float, "y": float} | None,
            "error": str (on failure)
        }
    """
    if not VWORLD_API_KEY:
        return {
            "success": False,
            "error": "VWORLD_API_KEY not configured. "
                     "Get a key at https://www.vworld.kr and set VWORLD_API_KEY env var.",
            "address": address,
            "pnu": None,
        }

    # Step 1: Geocode address (try PARCEL type for 지번, fallback to ROAD)
    for addr_type in ("PARCEL", "ROAD"):
        result = _vworld_geocode(address, addr_type)
        if result and result.get("response", {}).get("status") == "OK":
            return _parse_geocode_result(result, address)

    return {
        "success": False,
        "error": f"Vworld geocoding failed: no results for '{address}'",
        "address": address,
        "pnu": None,
    }


def _vworld_geocode(address: str, addr_type: str) -> dict | None:
    """Call Vworld geocoding API."""
    params = {
        "service": "address",
        "request": "getCoord",
        "key": VWORLD_API_KEY,
        "address": address,
        "type": addr_type,
        "format": "json",
        "crs": "EPSG:4326",
        "refine": "true",
    }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(VWORLD_GEOCODE_URL, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        logger.error("Vworld API unreachable")
        return None
    except Exception as e:
        logger.error(f"Vworld geocode failed: {e}")
        return None


def _parse_geocode_result(data: dict, original_address: str) -> dict:
    """Parse Vworld geocode response into our format."""
    try:
        response = data["response"]
        if response.get("status") != "OK":
            return {
                "success": False,
                "error": f"Vworld status: {response.get('status')}",
                "address": original_address,
                "pnu": None,
            }

        result = response["result"]
        point = result["point"]
        x = float(point["x"])
        y = float(point["y"])

        # Extract PNU from refined.structure.level4LC (19-digit code)
        pnu = None
        refined = response.get("refined", {})
        structure = refined.get("structure", {})
        level4lc = structure.get("level4LC", "")
        if validate_pnu(level4lc):
            pnu = level4lc

        geocoded_text = refined.get("text", "")

        return {
            "success": True,
            "address": original_address,
            "pnu": pnu,
            "coordinates": {"x": x, "y": y},
            "geocoded_address": geocoded_text,
        }

    except (KeyError, TypeError, ValueError) as e:
        return {
            "success": False,
            "error": f"Failed to parse Vworld response: {e}",
            "address": original_address,
            "pnu": None,
        }
