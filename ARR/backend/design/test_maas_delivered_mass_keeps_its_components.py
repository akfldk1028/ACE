"""The delivered mass keeps the authored program's components - when the form has them.

The authored source for a cultural program is a composition: a gallery hall, a
public hall, an entry ramp, each with its own footprint and height band. Their
plan shares land at 0.43/0.38/0.10/0.09 - squarely inside cultural's
(0.32, 0.75) hierarchy band. What used to be delivered was one role at share
1.000 on every one of 128 masses, because materialization stamped the single
largest authored role onto every piece it produced.

The discriminator here is the neck. Two lobes joined by a short waist are two
components and are labelled as such. A convex plate covers exactly the same
authored regions and could be cut by any ratio, but it has no neck, so it stays
one component and keeps failing the hierarchy gate - which is the honest
outcome for a box, and the reason this is not a relabelling.
"""

from shapely.geometry import box
from shapely.ops import unary_union

from django.test import SimpleTestCase

from design.maas.geometry_language.source_bridge import (
    _articulated_component_parts,
    _authored_component_regions,
)
from design.maas.source_geometry.ir import SourceMass, SourceVolume


IDENTITY = (
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 1.0),
)
WEST = box(0.0, 0.0, 20.0, 20.0)
EAST = box(30.0, 0.0, 50.0, 20.0)
# A 4 m wide neck joining the two halls: one connected body, two lobes.
NECK = box(20.0, 8.0, 30.0, 12.0)


def _source(volumes):
    return SourceMass(
        name="component-source",
        footprint=unary_union([volume.footprint for volume in volumes]),
        volumes=tuple(volumes),
    )


def _component(role, footprint, bottom=0.0, top=1.0):
    return SourceVolume(role, footprint, bottom, top, "geometry_program")


class DeliveredMassKeepsItsComponentsTests(SimpleTestCase):
    def _regions(self, source, *, bottom=0.0, top=0.5):
        return _authored_component_regions(
            source,
            matrix=IDENTITY,
            bottom_fraction=bottom,
            top_fraction=top,
        )

    def test_two_lobes_joined_by_a_neck_keep_both_roles(self):
        source = _source([
            _component("west_gallery_hall", WEST),
            _component("east_public_hall", EAST),
        ])
        delivered = unary_union([WEST, NECK, EAST])

        assigned = _articulated_component_parts(
            delivered,
            self._regions(source),
            fallback_role="west_gallery_hall",
        )

        self.assertEqual(
            {"west_gallery_hall", "east_public_hall"},
            {role for role, _piece in assigned},
        )

    def test_a_convex_plate_over_the_same_components_stays_one_role(self):
        """The box could be cut by any ratio. It has no neck, so it is not."""

        source = _source([
            _component("west_gallery_hall", WEST),
            _component("east_public_hall", EAST),
        ])
        plate = box(0.0, 0.0, 50.0, 20.0)

        assigned = _articulated_component_parts(
            plate,
            self._regions(source),
            fallback_role="west_gallery_hall",
        )

        self.assertEqual(1, len(assigned))
        self.assertEqual("west_gallery_hall", assigned[0][0])

    def test_the_pieces_still_tile_the_delivered_part(self):
        """Roles may not add or lose area: this is a partition, not a redraw."""

        source = _source([
            _component("west_gallery_hall", WEST),
            _component("east_public_hall", EAST),
        ])
        delivered = unary_union([WEST, NECK, EAST])

        assigned = _articulated_component_parts(
            delivered,
            self._regions(source),
            fallback_role="west_gallery_hall",
        )

        self.assertAlmostEqual(
            float(delivered.area),
            float(unary_union([piece for _role, piece in assigned]).area),
            places=3,
        )

    def test_a_component_outside_the_band_is_not_offered(self):
        """An entry ramp that stops at 0.2 has no say about the top floor."""

        source = _source([
            _component("west_gallery_hall", WEST),
            _component("entry_ramp", EAST, bottom=0.0, top=0.2),
        ])

        roles = {
            role
            for role, _region in self._regions(source, bottom=0.5, top=1.0)
        }

        self.assertEqual({"west_gallery_hall"}, roles)

    def test_a_sliver_does_not_become_a_component(self):
        source = _source([
            _component("west_gallery_hall", WEST),
            _component("east_public_hall", box(19.5, 0.0, 20.5, 20.0)),
        ])

        assigned = _articulated_component_parts(
            WEST,
            self._regions(source),
            fallback_role="west_gallery_hall",
        )

        self.assertEqual(1, len(assigned))
