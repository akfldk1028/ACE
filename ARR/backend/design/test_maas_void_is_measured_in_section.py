"""The void axis has to see a court that a roof sits over.

`plan_void_ratio` unioned every volume record regardless of height and measured
the open share of that one flattened figure. That is the same mistake as
unioning every triangle of a mesh into a silhouette: whatever sits above an
opening closes it again. Measured on a 40x24x18 reference solid at their
strongest accepted settings, five of the ten BOOK operatives read exactly 0.000
flattened - carve, grade, notch, fracture and extract - while their sections
read 0.322, 0.555, 0.245, 0.144 and 0.314. The axis could not see half the
language, which is why `porous_field` never appeared in a delivered grid and
the void column was driven by `branch` and `rotate` alone.

Sections fix that without introducing a sampling height: the bands are the
volumes' own level boundaries, and each band is weighted by its thickness.
"""

from django.test import SimpleTestCase

from design.maas.design_space import delivered_void_band
from design.maas.program_massing.semantic_projection import project_spatial_roles


def _ring(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]


def _volume(x0, y0, x1, y1, bottom, top):
    return {
        "bottom_height": bottom,
        "top_height": top,
        "geometry": {"type": "Polygon", "coordinates": [_ring(x0, y0, x1, y1)]},
    }


def _feature(*volumes):
    return {
        "type": "Feature",
        "properties": {"mass_volumes": list(volumes)},
        "geometry": None,
    }


def _void(*volumes):
    projection = project_spatial_roles(_feature(*volumes))
    return float(projection.get("plan_void_ratio") or 0.0)


class VoidIsMeasuredInSectionTests(SimpleTestCase):
    def test_a_plain_box_is_solid(self):
        self.assertAlmostEqual(0.0, _void(_volume(0, 0, 40, 24, 0, 18)), places=3)

    def test_a_court_under_a_roof_is_not_reported_solid(self):
        """Two bars with a gap, capped by a slab that spans both.

        Flattened, the cap fills the gap and the figure reads solid. In section
        the lower band is open and only the top band is closed.
        """

        court = _void(
            _volume(0, 0, 40, 9, 0, 12),
            _volume(0, 15, 40, 24, 0, 12),
            _volume(0, 0, 40, 24, 12, 18),
        )

        self.assertGreater(court, 0.0)
        self.assertNotEqual("solid_body", delivered_void_band(court).band_id)

    def test_the_open_band_counts_for_its_own_thickness(self):
        """Two thirds open, one third capped -> about two thirds of the gap.

        The gap is 6 of 24 across, so an open section reads 0.25; over 12 of the
        18 metres that averages to about 0.167.
        """

        measured = _void(
            _volume(0, 0, 40, 9, 0, 12),
            _volume(0, 15, 40, 24, 0, 12),
            _volume(0, 0, 40, 24, 12, 18),
        )

        self.assertAlmostEqual(0.25 * 12.0 / 18.0, measured, places=2)

    def test_a_court_open_to_the_sky_reads_the_same_at_every_band(self):
        through = _void(
            _volume(0, 0, 40, 9, 0, 18),
            _volume(0, 15, 40, 24, 0, 18),
        )

        self.assertAlmostEqual(0.25, through, places=3)

    def test_a_rotated_solid_still_reads_zero(self):
        """The tightest rectangle, not the axis-aligned one - this was the
        earlier contamination and the section measure must not reintroduce it."""

        import math

        angle = math.radians(37.0)
        corners = [(0.0, 0.0), (40.0, 0.0), (40.0, 24.0), (0.0, 24.0)]
        turned = [
            [
                x * math.cos(angle) - y * math.sin(angle),
                x * math.sin(angle) + y * math.cos(angle),
            ]
            for x, y in corners
        ]
        volume = {
            "bottom_height": 0.0,
            "top_height": 18.0,
            "geometry": {"type": "Polygon", "coordinates": [turned + [turned[0]]]},
        }

        self.assertAlmostEqual(0.0, _void(volume), places=3)

    def test_a_single_level_building_is_still_measurable(self):
        """One band is the whole building; it must not fall through to zero."""

        measured = _void(
            _volume(0, 0, 40, 9, 0, 18),
            _volume(0, 15, 40, 24, 0, 18),
        )

        self.assertGreater(measured, 0.0)
