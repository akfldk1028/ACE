"""Take one word out of the sentence and see whether the building notices.

`postcondition` asks whether a word changed the mass *at the moment it was
said* - it runs the sentence forward and compares consecutive frames, at the
size it was authored, before the growth loop and before the legal clip. That is
the right question for finding a word that was never doing anything, and it is
the wrong one for finding a word whose effect does not survive to the drawing.

The two come apart because everything after the sentence can undo it. `fill`
grows the composition toward the parcel's own capacity; the compiler cuts every
band to the sunlight envelope. A shear measured 0.35 unclipped and 0.04 after
the clip on the same scheme, which was recorded at the time as the gate being
right - the two masses really were nearly the same building. So a word can pass
the postcondition and still be absent from what a person is shown.

This asks the other question, the one the critics are actually answering:

    remove this word from the sentence, run the whole pipeline again, and
    compare the two delivered masses.

A word that changes nothing when removed is not in the building, whatever it
did in the middle of the sentence. Removing a word can also break the words
after it - `on: "west_islands"` names a part that a removed `split` never made,
and `_scope` then finds nothing and the operation is silent. That is not a flaw
in the measurement, it is the measurement: a word the rest of the sentence
depends on is load-bearing, and the number says so.

Cost is one extra pipeline run per word, at sentence level rather than per
delivered variant - about three runs for a typical sentence. The coverage and
siting copies of one sentence share its words, so they share this number.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from design.maas.source_geometry.ir import SourceMass

from .compile import compile_matrix_form
from .execute import execute as execute_parti
from .fill import fill_to_site
from .postcondition import changed_share


@dataclass(frozen=True)
class Ablation:
    """What each word is worth to the mass that gets drawn."""

    declared: tuple[str, ...]
    removed_share: tuple[float, ...]

    @property
    def force(self) -> float:
        """The mean word. Not the weakest: a sentence is allowed one quiet word
        beside a loud one, and the postcondition gate already refuses a word
        that does nothing at all."""

        if not self.removed_share:
            return 0.0
        return sum(self.removed_share) / len(self.removed_share)

    @property
    def idle(self) -> tuple[str, ...]:
        """Words the delivered building does not notice the loss of."""

        return tuple(
            verb
            for verb, share in zip(self.declared, self.removed_share)
            if share < IDLE_BELOW
        )

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_ablation.v1",
            "declared": list(self.declared),
            "removed_share": [round(value, 4) for value in self.removed_share],
            "force": round(self.force, 4),
            "idle": list(self.idle),
        }


# Below this the delivered mass is the same drawing without the word. The same
# floor `postcondition` uses, for the same reason and against the same corpus
# reading - a move under a twentieth of the building is not a decision anyone
# can see. Reported, not gated: this module measures, and whether it should
# refuse anything is a question for evidence that does not exist yet.
IDLE_BELOW = 0.05


def _delivered(
    parti, *, buildable, axis, height_m, site, storey_height_m: float
) -> SourceMass | None:
    """The mass this sentence actually puts on the sheet, clip and growth included."""

    if not parti.ops:
        return None
    form = execute_parti(
        parti, buildable=buildable, axis=axis, height_m=height_m,
        storey_height_m=storey_height_m,
    )
    if form is None:
        return None
    filled = fill_to_site(form, site)
    return compile_matrix_form(
        filled.fit.form, storey_height_m=storey_height_m, allowed_at=site.plan_at
    )


def ablate(
    parti, *, buildable, axis, height_m, site, storey_height_m: float
) -> Ablation:
    """One run per word, each with that word taken out."""

    declared = tuple(op.verb for op in parti.ops)
    whole = _delivered(
        parti, buildable=buildable, axis=axis, height_m=height_m,
        site=site, storey_height_m=storey_height_m,
    )
    if whole is None:
        return Ablation(declared, tuple(0.0 for _ in declared))

    shares: list[float] = []
    for index in range(len(parti.ops)):
        shorter = replace(
            parti,
            ops=tuple(op for position, op in enumerate(parti.ops) if position != index),
        )
        without = _delivered(
            shorter, buildable=buildable, axis=axis, height_m=height_m,
            site=site, storey_height_m=storey_height_m,
        )
        # A sentence that will not stand without this word is entirely this
        # word's, which is the strongest thing the measure can say.
        shares.append(1.0 if without is None else changed_share(whole, without))
    return Ablation(declared, tuple(shares))


__all__ = ["Ablation", "ablate", "IDLE_BELOW"]
