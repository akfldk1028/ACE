"""Paper and code provenance for MAAS second-stage preference distillation."""

from __future__ import annotations

from typing import Any


PREFERENCE_PAPER_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "id": "ppd_cvpr_2025",
        "title": "Personalized Preference Fine-tuning of Diffusion Models",
        "paper_url": "https://arxiv.org/abs/2501.06655",
        "code_url": "https://github.com/Asap7772/Personalized-Text-To-Image-Diffusion",
        "local_code_path": "clone/Personalized-Text-To-Image-Diffusion",
        "local_commit": "fe3835f",
        "maas_adaptation": "few-shot pairwise preference examples and VLM preference profile extraction",
        "limitation": "public code includes only the VLM component, not diffusion fine-tuning",
    },
    {
        "id": "visionreward_2024",
        "title": "VisionReward: Fine-Grained Multi-Dimensional Human Preference Learning for Image and Video Generation",
        "paper_url": "https://arxiv.org/abs/2412.21059",
        "code_url": "https://github.com/zai-org/VisionReward",
        "local_code_path": "clone/VisionReward",
        "local_commit": "511960d",
        "maas_adaptation": "architecture-specific VLM QA checklist with weighted concept scoring",
        "limitation": "generic image reward questions must be replaced by architecture-massing questions",
    },
    {
        "id": "aesthetiq_cvpr_2025",
        "title": "AesthetiQ: Enhancing Graphic Layout Design via Aesthetic-Aware Preference Alignment",
        "paper_url": "https://arxiv.org/abs/2503.00591",
        "code_url": "",
        "local_code_path": "",
        "local_commit": "",
        "maas_adaptation": "filter candidates before preference alignment; use pairwise VLM preference after quality gates",
        "limitation": "official code repository not found during 2026-07-08 audit",
    },
    {
        "id": "designpref_2025",
        "title": "DesignPref: Capturing Personal Preferences in Visual Design Generation",
        "paper_url": "https://arxiv.org/abs/2511.20513",
        "code_url": "",
        "local_code_path": "",
        "local_commit": "",
        "maas_adaptation": "designer preference is subjective, so professor/user pairwise calibration is required",
        "limitation": "official code repository not found during 2026-07-08 audit",
    },
)


def paper_source_summary() -> list[dict[str, Any]]:
    return [dict(item) for item in PREFERENCE_PAPER_SOURCES]


__all__ = ["PREFERENCE_PAPER_SOURCES", "paper_source_summary"]

