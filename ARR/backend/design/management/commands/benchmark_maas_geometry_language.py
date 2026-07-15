"""Compile and render the recursive architectural geometry language probes."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageDraw

from design.maas.geometry_language import (
    architectural_shape_programs,
    compilation_gate,
    compile_geometry_program,
    program_cost,
    reference_language_programs,
    render_compilation_preview,
)


class Command(BaseCommand):
    help = "Compile the 18 procedural mass families and supplied-photo language probes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default="docs/playwright/design-route-live-verify/geometry-language",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"]).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        shape_records, shape_previews = self._compile_group(
            architectural_shape_programs(), output_dir / "shapes"
        )
        references = reference_language_programs()
        reference_records, reference_previews = self._compile_group(
            references.values(), output_dir / "references"
        )
        _contact_sheet(shape_previews, output_dir / "maas-geometry-language-18.png", columns=3)
        _contact_sheet(reference_previews, output_dir / "maas-reference-language-3.png", columns=3)
        unique_hashes = len({record["geometry_hash"] for record in shape_records if record["geometry_hash"]})
        visual_pairs = _visual_near_duplicate_pairs(shape_previews, threshold=0.10)
        minimum_visual_distance = _minimum_visual_distance(shape_previews)
        summary = {
            "schema_version": "arr.maas.geometry_language_benchmark.v1",
            "status": "PASS" if len(shape_records) == 18 and unique_hashes == 18 and not visual_pairs and all(row["gate_status"] == "PASS" for row in shape_records) else "FAIL",
            "statement": "Compiler diversity proves distinct solids, not competition-grade design quality.",
            "shape_count": len(shape_records),
            "unique_geometry_count": unique_hashes,
            "visual_hash_method": "four_view_dhash_32x24",
            "visual_near_duplicate_threshold": 0.10,
            "visual_near_duplicate_pairs": visual_pairs,
            "minimum_visual_distance": round(minimum_visual_distance, 6),
            "visual_language_verdict": "PASS" if not visual_pairs else "FAIL",
            "reference_language_count": len(reference_records),
            "shapes": shape_records,
            "reference_languages": reference_records,
        }
        summary_path = output_dir / "maas-geometry-language-summary.json"
        temporary = summary_path.with_suffix(".tmp.json")
        temporary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(summary_path)
        if summary["status"] != "PASS":
            raise CommandError(f"geometry language benchmark failed; see {summary_path}")
        self.stdout.write(self.style.SUCCESS(
            f"18/18 compiled, {unique_hashes}/18 unique solids; {summary_path}"
        ))

    def _compile_group(self, programs, preview_dir: Path):
        preview_dir.mkdir(parents=True, exist_ok=True)
        records = []
        previews = []
        for index, program in enumerate(programs, 1):
            result = compile_geometry_program(program)
            gate_issues = compilation_gate(result)
            preview_path = preview_dir / f"{index:02d}-{program.name}.png"
            if result.status == "compiled":
                render_compilation_preview(result, preview_path, title=f"{index:02d} {program.name}")
                previews.append((program.name, preview_path))
            records.append({
                "index": index,
                "name": program.name,
                "program_hash": program.program_hash(),
                "geometry_hash": result.geometry_hash,
                "compile_status": result.status,
                "gate_status": "PASS" if not gate_issues else "FAIL",
                "gate_issues": [issue.to_dict() for issue in gate_issues],
                "operators": [node.operator for node in program.topological_nodes()],
                "program_cost": program_cost(program, result).to_dict(),
                "metrics": result.metrics,
                "preview_path": str(preview_path),
            })
        return records, previews


def _contact_sheet(items, output_path: Path, *, columns: int) -> None:
    card_width, card_height = 450, 365
    rows = max(1, (len(items) + columns - 1) // columns)
    sheet = Image.new("RGB", (card_width * columns, card_height * rows), "#e8eef5")
    draw = ImageDraw.Draw(sheet)
    for index, (name, path) in enumerate(items):
        row, column = divmod(index, columns)
        with Image.open(path) as image:
            thumbnail = image.convert("RGB").resize((450, 340), Image.Resampling.LANCZOS)
        x, y = column * card_width, row * card_height
        sheet.paste(thumbnail, (x, y))
        draw.rectangle((x, y + 340, x + card_width, y + card_height), fill="#ffffff")
        draw.text((x + 9, y + 347), f"{index + 1:02d} {name[:56]}", fill="#172033")
    temporary = output_path.with_suffix(".tmp.png")
    sheet.save(temporary)
    temporary.replace(output_path)


def _difference_hash(path: Path) -> tuple[bool, ...]:
    with Image.open(path) as source:
        image = source.convert("L").resize((33, 24), Image.Resampling.LANCZOS)
    pixels = list(image.getdata())
    return tuple(
        pixels[y * 33 + x + 1] > pixels[y * 33 + x]
        for y in range(24)
        for x in range(32)
    )


def _visual_distance(left: tuple[bool, ...], right: tuple[bool, ...]) -> float:
    return sum(a != b for a, b in zip(left, right)) / max(1, len(left))


def _visual_near_duplicate_pairs(items, *, threshold: float):
    hashes = [(name, _difference_hash(path)) for name, path in items]
    pairs = []
    for index, (left_name, left_hash) in enumerate(hashes):
        for right_name, right_hash in hashes[:index]:
            distance = _visual_distance(left_hash, right_hash)
            if distance < threshold:
                pairs.append({"left": right_name, "right": left_name, "distance": round(distance, 6)})
    return pairs


def _minimum_visual_distance(items) -> float:
    hashes = [_difference_hash(path) for _name, path in items]
    distances = [
        _visual_distance(left, right)
        for index, left in enumerate(hashes)
        for right in hashes[:index]
    ]
    return min(distances) if distances else 1.0
