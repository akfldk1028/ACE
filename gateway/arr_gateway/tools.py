"""Tool handlers — Hermes 규약: args dict + **kwargs 받아 JSON 문자열 반환.

호출 대상: AG-light Cloudflare Worker (유일한 public API, 메모리 박제).
ARR Backend Django는 ARR Frontend 웹 전용 — Hermes 경로는 AG-light 직접.

Hermes handler 규약:
- 시그니처: def handler(args: dict, **kwargs) -> str
- 항상 JSON string 반환 (에러도)
- 절대 raise 하지 말 것 (catch 후 error JSON 반환)
"""
import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

AGLIGHT_URL = os.getenv(
    "AGLIGHT_URL",
    "https://law-light-api.clickaround8.workers.dev",
).rstrip("/")

# Module-level client — connection pooling, 매 호출마다 새 TCP 안 만듦
_HTTP_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)
_client = httpx.Client(timeout=_HTTP_TIMEOUT)


def land_analyst(args: dict, **kwargs) -> str:
    """토지 규제 분석 — AG-light Worker 호출.

    Args:
        args: {"pnu_or_address": "강남구 역삼동 677" 또는 PNU 19자리}
        kwargs: Hermes forward-compat (task_id, session_id 등 — 미사용)

    Returns:
        JSON string. 성공: AG-light /land/analyze 응답 (pnu/regulations/setback_lines/law_articles).
        실패: {"error": "..."}
    """
    pnu_or_address = (args.get("pnu_or_address") or "").strip()
    if not pnu_or_address:
        logger.warning("land_analyst: pnu_or_address empty")
        return json.dumps({"error": "pnu_or_address required"}, ensure_ascii=False)

    url = f"{AGLIGHT_URL}/land/analyze"
    payload = {"input": pnu_or_address, "include_law": True}
    logger.info("land_analyst → POST %s (input=%s)", url, pnu_or_address)

    try:
        r = _client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        logger.info("land_analyst ← %d (PNU=%s)", r.status_code, data.get("pnu", {}).get("pnu", "?") if isinstance(data, dict) else "?")
        return json.dumps(data, ensure_ascii=False)
    except httpx.TimeoutException as e:
        logger.error("land_analyst timeout: %s", e)
        return json.dumps({"error": f"AG-light 타임아웃: {e}"}, ensure_ascii=False)
    except httpx.HTTPStatusError as e:
        logger.error("land_analyst HTTP %d: %s", e.response.status_code, e)
        return json.dumps(
            {"error": f"AG-light HTTP {e.response.status_code}", "body": e.response.text[:300]},
            ensure_ascii=False,
        )
    except httpx.HTTPError as e:
        logger.error("land_analyst HTTP error: %s", e)
        return json.dumps({"error": f"AG-light 호출 실패: {e}"}, ensure_ascii=False)
    except json.JSONDecodeError as e:
        logger.error("land_analyst JSON parse: %s", e)
        return json.dumps({"error": f"응답 JSON 파싱 실패: {e}"}, ensure_ascii=False)
    except Exception as e:
        logger.exception("land_analyst unexpected error")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
