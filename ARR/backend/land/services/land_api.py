"""
Land API - interfaces with data.go.kr public APIs.

Phase 3: actual API implementation (requires DATA_GO_KR_SERVICE_KEY).
Currently returns stub/fixture data.

APIs to integrate:
- 토지이용규제정보 (land use regulation)
- 건축물대장 (building ledger)
- 개별공시지가 (official land price)
"""

import logging

logger = logging.getLogger(__name__)


def get_land_use_info(pnu: str) -> dict:
    """
    Fetch land use regulation info from data.go.kr.

    Phase 3 stub: returns fixture data structure.

    Args:
        pnu: 19-digit PNU code

    Returns:
        {
            "success": bool,
            "pnu": str,
            "zones": [str],  # list of zoning zone names
            "land_area_m2": float | None,
            "official_land_price": int | None,
            "land_use_situation": str,
            "source": "stub" | "api"
        }
    """
    logger.info(f"land_api.get_land_use_info(pnu={pnu}) - stub mode")

    return {
        "success": True,
        "pnu": pnu,
        "zones": [],
        "land_area_m2": None,
        "official_land_price": None,
        "land_use_situation": "",
        "source": "stub",
        "message": "data.go.kr API not yet connected (Phase 3). "
                   "Provide zones manually via 'zones' field in request body.",
    }
