"""Compose program assemblies with executable BOOK operations.

Program templates establish use-specific roles (hall, service spine, entry,
public anchor).  BOOK operations then mutate the dominant occupiable mass in
the compiler while subordinate roles remain available to program validation.
The note is a typed compiler boundary, not a name-based geometry shortcut.
"""

from __future__ import annotations

from collections.abc import Iterable

from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.grammar.vocab import AGGREGATION_VERBS, BOOK_BASE_VERBS
from design.maas.grammar.parameter_schema import CATEGORICAL_PARAMETER_VALUES, PARAMETER_BOUNDS, PARAMETERS_BY_VERB, bounded_parameter
from design.maas.book_language.semantics import semantics_for
from .book_scope import BOOK_SCOPE_VERB, BookProjectionScope, projection_scope
from .section_graph import (
    mutate_program_section_graph_for_book,
    program_section_graph_from_sequence,
    replace_program_section_graph_note,
)


BOOK_PROJECTION_NOTE = "book_projection_start="
BOOK_EXECUTABLE_VERBS = BOOK_BASE_VERBS | AGGREGATION_VERBS


def compose_program_with_book_operations(
    program_sequence: VerbSequence,
    operations: Iterable[VerbCall],
    *,
    name_suffix: str | None = None,
    base_volume_label: str = "1/1",
    orientation: str = "long_axis",
) -> VerbSequence:
    """Append typed operations after a program seed and mark their boundary."""
    appended = tuple(operations)
    if not appended:
        return program_sequence
    unsupported = [call.verb for call in appended if call.verb not in BOOK_EXECUTABLE_VERBS]
    if unsupported:
        raise ValueError(f"BOOK projection only accepts base operative verbs: {unsupported}")
    start = len(program_sequence.calls)
    scope = projection_scope(base_volume_label, orientation)
    scope_call = VerbCall(BOOK_SCOPE_VERB, {
        "base_volume_label": scope.label,
        "orientation": scope.orientation,
    })
    notes = tuple(program_sequence.notes)
    section_graph = program_section_graph_from_sequence(program_sequence)
    if section_graph:
        section_graph = mutate_program_section_graph_for_book(
            section_graph,
            appended,
            scope_label=scope.label,
            scope_fraction=scope.requested_fraction,
        )
        notes = replace_program_section_graph_note(notes, section_graph)
    suffix = name_suffix or "_".join(call.verb for call in appended)
    return VerbSequence(
        name=f"{program_sequence.name}__book_{suffix}",
        label=f"{program_sequence.label} + BOOK {' + '.join(call.verb for call in appended)}",
        calls=(*program_sequence.calls, scope_call, *appended),
        notes=(*notes, f"{BOOK_PROJECTION_NOTE}{start}"),
    )


def book_projection_calls(sequence: VerbSequence) -> tuple[VerbCall, ...]:
    """Return only explicitly marked BOOK calls; ordinary seeds return none."""
    raw = next((note.removeprefix(BOOK_PROJECTION_NOTE) for note in sequence.notes if note.startswith(BOOK_PROJECTION_NOTE)), "")
    try:
        start = int(raw)
    except (TypeError, ValueError):
        return ()
    if start < 1 or start >= len(sequence.calls):
        return ()
    calls = tuple(call for call in sequence.calls[start:] if call.verb != BOOK_SCOPE_VERB)
    return calls if all(call.verb in BOOK_EXECUTABLE_VERBS for call in calls) else ()


def book_projection_scope(sequence: VerbSequence) -> BookProjectionScope:
    raw = next((note.removeprefix(BOOK_PROJECTION_NOTE) for note in sequence.notes if note.startswith(BOOK_PROJECTION_NOTE)), "")
    try:
        start = int(raw)
        call = sequence.calls[start]
    except (IndexError, TypeError, ValueError):
        return projection_scope()
    if call.verb != BOOK_SCOPE_VERB:
        return projection_scope()
    return projection_scope(
        str(call.params.get("base_volume_label") or "1/1"),
        str(call.params.get("orientation") or "long_axis"),
    )


def _typed_variant(verb: str, index: int, *, active_parameters: frozenset[str] | None) -> VerbCall:
    fractions = (0.34, 0.50, 0.66, 0.42, 0.58)
    params: dict[str, object] = {}
    for name in PARAMETERS_BY_VERB.get(verb, ()):
        active = active_parameters is None or name in active_parameters
        if name in CATEGORICAL_PARAMETER_VALUES:
            values = CATEGORICAL_PARAMETER_VALUES[name]
            params[name] = values[index % len(values)] if active else values[0]
            continue
        if name not in PARAMETER_BOUNDS:
            continue
        low, high = PARAMETER_BOUNDS[name]
        fraction = fractions[index % len(fractions)] if active else 0.50
        params[name] = bounded_parameter(name, low + (high - low) * fraction)
    return VerbCall(verb, params)


def book_operation_variants(verb: str, *, count: int = 3) -> tuple[VerbCall, ...]:
    """Create normalized parameter probes from the shared typed schema.

    These are bounded compiler/search probes, not parcel-coordinate recipes.
    Agent/VLM authored values can replace them through the same parameter
    contract after the operation proves executable for a program.
    """
    if verb not in BOOK_BASE_VERBS:
        raise ValueError(f"unknown BOOK base operative: {verb}")
    count = max(1, min(5, int(count)))
    semantics = semantics_for(verb)
    variation_parameters = frozenset(semantics.variation_parameters)
    return tuple(_typed_variant(verb, index, active_parameters=variation_parameters) for index in range(count))


def book_sentence_variants(verbs: Iterable[str], *, count: int = 1) -> tuple[tuple[VerbCall, ...], ...]:
    """Materialize a BOOK execution sentence in its recorded operation order."""
    execution = tuple(str(verb) for verb in verbs)
    unsupported = [verb for verb in execution if verb not in BOOK_EXECUTABLE_VERBS]
    if not execution or unsupported:
        raise ValueError(f"invalid BOOK execution sentence: {unsupported or execution}")
    count = max(1, min(3, int(count)))
    result: list[tuple[VerbCall, ...]] = []
    for index in range(count):
        calls = []
        for verb in execution:
            active = frozenset(semantics_for(verb).variation_parameters) if verb in BOOK_BASE_VERBS else None
            calls.append(_typed_variant(verb, index, active_parameters=active))
        result.append(tuple(calls))
    return tuple(result)


__all__ = ["BOOK_EXECUTABLE_VERBS", "BOOK_PROJECTION_NOTE", "book_operation_variants", "book_projection_calls", "book_projection_scope", "book_sentence_variants", "compose_program_with_book_operations"]
