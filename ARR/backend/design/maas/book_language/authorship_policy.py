"""Bounded paid-authorship policy for BOOK portfolio generation."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from design.maas.geometry_language import synthesis_requests_from_program_profile


MAX_LIVE_LLM_AUTHORED_PROGRAMS = 12


def bounded_live_llm_synthesis_requests(
    building_type: str,
    *,
    source_seed_names: Iterable[str],
    target_count: int,
    prior_requests: Iterable[Mapping[str, Any]] = (),
) -> tuple[dict[str, Any], ...]:
    """Create one paid LLM request; exact-solid VLM remains a later stage."""

    source_seed = next(
        (str(name) for name in source_seed_names if str(name)),
        "",
    )
    if not source_seed:
        return ()
    authored_count = max(
        1,
        min(MAX_LIVE_LLM_AUTHORED_PROGRAMS, int(target_count)),
    )
    profile_requests = synthesis_requests_from_program_profile(
        building_type,
        source_seeds=(source_seed,),
        candidates_per_lineage=authored_count,
    )
    if not profile_requests:
        return ()
    prior = tuple(
        dict(request)
        for request in prior_requests
        if isinstance(request, Mapping)
    )
    intent_tags = list(dict.fromkeys(
        str(tag)
        for request in prior
        for tag in (request.get("intent_tags") or ())
        if str(tag)
    ))
    request = dict(profile_requests[0])
    if intent_tags:
        request["intent_tags"] = intent_tags
    return ({
        **request,
        "live_llm_author": True,
        "llm_author_only": True,
        "llm_author_count": authored_count,
        "live_vlm_revision": False,
        "synthesis_request_source": "bounded_live_llm_portfolio_author",
    },)


__all__ = [
    "MAX_LIVE_LLM_AUTHORED_PROGRAMS",
    "bounded_live_llm_synthesis_requests",
]
