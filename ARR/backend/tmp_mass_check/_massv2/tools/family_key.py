"""Workspace alias - the composition family moved into the package.

The key started life here beside the board curator; the day the audit showed
the cell selector seating one family six times, the selector needed it too,
and a quota's owner belongs in the code it polices. Everything imports from
`design.maas.massv2.family` now; this file keeps old tool invocations alive.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from design.maas.massv2.family import (  # noqa: E402,F401
    FAMILY_OF_VERB,
    OPENERS,
    QUIET,
    family_key,
    family_tag,
    one_per_family,
)
