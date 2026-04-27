"""Tool handlers — Hermes 규약: args dict + **kwargs 받아 JSON 문자열 반환.

호출 대상: ARR Backend Django (Railway).
- AG-light Worker는 health OK이지만 /land/analyze가 외부 API(Vworld) hang 시 60초 timeout.
- ARR Backend Django는 partial data 반환 + 짧은 timeout으로 robust.
- 2026-04-27 smoke test 결과로 결정 변경 (메모리 #6 보정됨).

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

ARR_BACKEND_URL = os.getenv(
    "ARR_BACKEND_URL",
    "https://arr-backend-production.up.railway.app",
).rstrip("/")

# Module-level client — connection pooling, 매 호출마다 새 TCP 안 만듦
_HTTP_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)
_client = httpx.Client(timeout=_HTTP_TIMEOUT)


def land_analyst(args: dict, **kwargs) -> str:
    """토지 규제 분석 — ARR Backend Django 호출.

    Args:
        args: {"pnu_or_address": "강남구 역삼동 677" 또는 PNU 19자리}
        kwargs: Hermes forward-compat (task_id, session_id 등 — 미사용)

    Returns:
        JSON string. 성공: ARR /land/analyze/ 응답 (pnu/regulations/zone_info/land_info/law_articles).
        실패: {"error": "..."}
    """
    pnu_or_address = (args.get("pnu_or_address") or "").strip()
    if not pnu_or_address:
        logger.warning("land_analyst: pnu_or_address empty")
        return json.dumps({"error": "pnu_or_address required"}, ensure_ascii=False)

    # PNU 19자리 숫자면 input_type=pnu, 아니면 address (Django 쪽에서 자동 판별도 함)
    is_pnu = pnu_or_address.isdigit() and len(pnu_or_address) == 19
    input_type = "pnu" if is_pnu else "address"

    url = f"{ARR_BACKEND_URL}/land/analyze/"
    payload = {"input": pnu_or_address, "input_type": input_type, "include_law": True}
    logger.info("land_analyst → POST %s (input=%s, type=%s)", url, pnu_or_address, input_type)

    try:
        r = _client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        pnu_str = data.get("pnu", {}).get("pnu", "?") if isinstance(data, dict) else "?"
        logger.info("land_analyst ← %d (PNU=%s)", r.status_code, pnu_str)
        return json.dumps(data, ensure_ascii=False)
    except httpx.TimeoutException as e:
        logger.error("land_analyst timeout: %s", e)
        return json.dumps({"error": f"ARR Backend 타임아웃: {e}"}, ensure_ascii=False)
    except httpx.HTTPStatusError as e:
        logger.error("land_analyst HTTP %d: %s", e.response.status_code, e)
        return json.dumps(
            {"error": f"ARR Backend HTTP {e.response.status_code}", "body": e.response.text[:300]},
            ensure_ascii=False,
        )
    except httpx.HTTPError as e:
        logger.error("land_analyst HTTP error: %s", e)
        return json.dumps({"error": f"ARR Backend 호출 실패: {e}"}, ensure_ascii=False)
    except json.JSONDecodeError as e:
        logger.error("land_analyst JSON parse: %s", e)
        return json.dumps({"error": f"응답 JSON 파싱 실패: {e}"}, ensure_ascii=False)
    except Exception as e:
        logger.exception("land_analyst unexpected error")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
