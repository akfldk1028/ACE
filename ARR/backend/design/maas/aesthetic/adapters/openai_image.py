"""OpenAI GPT Image adapter for MAAS aesthetic image-to-image generation."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from typing import Any

from ..contracts import ProviderResult, RenderedReference


class OpenAIImageAdapter:
    name = "gpt-image"

    def __init__(self, *, output_dir: str | Path | None = None) -> None:
        self.output_dir = Path(output_dir or Path("media") / "maas" / "aesthetic" / "generated")

    def generate(self, job: dict[str, Any], reference: RenderedReference) -> ProviderResult:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return _not_configured("OPENAI_API_KEY is not set.")
        reference_path = Path(reference.uri)
        if not reference_path.exists():
            return _not_configured(f"Reference image does not exist: {reference.uri}")

        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover - depends on deployment env
            return _not_configured(f"openai package unavailable: {exc}")

        prompt = job.get("prompt", {}).get("prompt") or ""
        negative = job.get("prompt", {}).get("negative_prompt") or ""
        reference_type = reference.metadata.get("reference_type") if isinstance(reference.metadata, dict) else None
        if reference_type == "multi_view_pack":
            reference_instruction = (
                "The input is a locked multi-view architectural massing sheet with front, right, back, left, axon, and top views. "
                "Generate one coherent photorealistic architectural facade/material concept for the same building across all views. "
                "Treat the output as a projection-ready facade texture atlas for the existing 3D mass: material scale, window rhythm, mullions, balcony depth, reveals, parapets, and corner returns must align across panels. "
                "Keep facade rhythm, material palette, floor lines, openings, corners, roofline, and massing steps consistent between panels. "
                "Replace the diagrammatic orange mass panels with credible finished architecture in each view; keep only the panel layout and locked silhouette. "
            )
        elif reference_type == "locked_mass_sheet":
            reference_instruction = (
                "The input is a locked four-view architectural MASS sheet containing isometric, opposite, top, and front views of the same building. "
                "Generate one coherent photorealistic facade and material proposal across every panel. "
                "Keep the sheet layout, every camera, and every MASS outline exactly aligned so the result remains directly comparable to the source. "
            )
        else:
            reference_instruction = "Edit this legal massing reference into a photorealistic projection-ready architectural facade concept. "
        full_prompt = (
            f"{reference_instruction}{prompt} "
            f"Use real architectural material detail, natural lighting, believable glazing, fine surface texture, and construction-scale facade proportions. "
            f"Design a refined facade composition with base-middle-top hierarchy, aligned floor datums, deep window reveals, corner-return continuity, parapet coping, and a clear entrance zone. "
            f"Strictly preserve the exact silhouette, footprint, roofline, height, floor count, and mass steps. "
            f"Do not make a freestanding beauty render, collage, wallpaper texture, repeated sticker windows, or change the building mass; the image must remain usable as facade texture evidence for the locked MAAS geometry. "
            f"Negative constraints: {negative}"
        )
        model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
        size = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{_safe_id(job)}.openai.png"
        evidence = {
            "model": model,
            "size": size,
            "reference_asset_id": reference.asset_id,
            "prompt_sha256": hashlib.sha256(full_prompt.encode("utf-8")).hexdigest(),
            "input_image_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
            "output_image_sha256": "",
            "request_id": "",
            "usage": {},
            "retry_count": 0,
        }

        try:
            client = OpenAI(api_key=api_key)
            with reference_path.open("rb") as image_file:
                raw_api = getattr(client.images, "with_raw_response", None)
                if raw_api is not None:
                    raw_response = raw_api.edit(
                        model=model,
                        image=image_file,
                        prompt=full_prompt,
                        size=size,
                        n=1,
                    )
                    response = raw_response.parse()
                    headers = getattr(raw_response, "headers", {}) or {}
                    evidence["request_id"] = str(
                        headers.get("x-request-id")
                        or headers.get("request-id")
                        or ""
                    )
                else:  # pragma: no cover - compatibility with older SDKs
                    response = client.images.edit(
                        model=model,
                        image=image_file,
                        prompt=full_prompt,
                        size=size,
                        n=1,
                    )
            usage = getattr(response, "usage", None)
            if usage is not None:
                evidence["usage"] = _serializable_usage(usage)
            item = response.data[0]
            b64_json = getattr(item, "b64_json", None)
            url = getattr(item, "url", None)
            if b64_json:
                output_path.write_bytes(base64.b64decode(b64_json))
                asset_uri = str(output_path)
                evidence["output_image_sha256"] = hashlib.sha256(
                    output_path.read_bytes()
                ).hexdigest()
            elif url:
                asset_uri = url
            else:
                return ProviderResult(
                    provider=self.name,
                    status="fail",
                    assets=[],
                    metadata=evidence,
                    issues=[{"code": "missing_image_payload", "message": "OpenAI response did not include b64_json or url."}],
                )
        except Exception as exc:  # pragma: no cover - network/provider behavior
            return ProviderResult(
                provider=self.name,
                status="fail",
                assets=[],
                metadata=evidence,
                issues=[{"code": "provider_error", "message": str(exc)}],
            )

        return ProviderResult(
            provider=self.name,
            status="complete",
            assets=[
                {
                    "asset_id": f"asset:maas-aesthetic-generated:{_safe_id(job)}:openai",
                    "uri": asset_uri,
                    "media_type": "image/png",
                    "source_bundle_id": job.get("source_bundle_id"),
                    "candidate_id": job.get("candidate_id"),
                    "legal_status_effect": "none",
                    "role": "generated_facade_image",
                }
            ],
            metadata=evidence,
        )


def _safe_id(job: dict[str, Any]) -> str:
    raw = f"{job.get('source_bundle_id') or 'bundle'}:{job.get('candidate_id') or 'candidate'}"
    return "".join(ch if ch.isalnum() else "_" for ch in raw)[-120:]


def _not_configured(message: str) -> ProviderResult:
    return ProviderResult(
        provider="gpt-image",
        status="not_configured",
        assets=[],
        metadata={},
        issues=[{"code": "provider_not_configured", "message": message}],
    )


def _serializable_usage(usage: Any) -> dict[str, Any]:
    if hasattr(usage, "model_dump"):
        value = usage.model_dump()
        return dict(value) if isinstance(value, dict) else {}
    if isinstance(usage, dict):
        return dict(usage)
    return {}


__all__ = ["OpenAIImageAdapter"]
