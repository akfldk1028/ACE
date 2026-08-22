"""The Matrix4 kernel feeds program hashes, so speed work must be bit-exact."""

from math import isfinite
from random import Random

from django.test import SimpleTestCase

from design.maas.geometry_language.affine_matrix import (
    compose_matrix4,
    rotation_matrix4,
    scale_matrix4,
    transform_point3,
    translation_matrix4,
    validate_matrix4,
    _multiply,
)


def _reference_validate(value):
    """The pre-optimization implementation, kept as the exactness oracle."""

    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("matrix4 must contain four rows")
    rows = []
    for row in value:
        if not isinstance(row, (list, tuple)) or len(row) != 4:
            raise ValueError("each matrix4 row must contain four numbers")
        numeric = tuple(float(item) for item in row)
        if not all(isfinite(item) for item in numeric):
            raise ValueError("matrix4 values must be finite")
        rows.append(numeric)
    expected = (0.0, 0.0, 0.0, 1.0)
    if any(abs(rows[3][index] - expected[index]) > 1e-9 for index in range(4)):
        raise ValueError("matrix4 must be affine with last row [0, 0, 0, 1]")
    return tuple(rows)


def _reference_multiply(left, right):
    """The pre-optimization implementation, kept as the exactness oracle."""

    return tuple(tuple(
        sum(left[row][inner] * right[inner][column] for inner in range(4))
        for column in range(4)
    ) for row in range(4))


def _random_affine(rng):
    return (
        tuple(rng.uniform(-40.0, 40.0) for _ in range(4)),
        tuple(rng.uniform(-40.0, 40.0) for _ in range(4)),
        tuple(rng.uniform(-40.0, 40.0) for _ in range(4)),
        (0.0, 0.0, 0.0, 1.0),
    )


class AffineMatrixExactnessTests(SimpleTestCase):
    def test_multiply_is_bit_identical_to_the_reference(self):
        rng = Random(20260810)

        for _ in range(400):
            left = _random_affine(rng)
            right = _random_affine(rng)
            self.assertEqual(
                _multiply(left, right),
                _reference_multiply(left, right),
            )

    def test_validate_is_bit_identical_to_the_reference(self):
        rng = Random(11)

        for _ in range(400):
            matrix = _random_affine(rng)
            self.assertEqual(validate_matrix4(matrix), _reference_validate(matrix))

    def test_validate_still_normalizes_lists_and_integers(self):
        matrix = [
            [1, 0, 0, 2],
            [0, 1, 0, 3],
            [0, 0, 1, 4],
            [0, 0, 0, 1],
        ]

        result = validate_matrix4(matrix)

        self.assertEqual(result, _reference_validate(matrix))
        self.assertIsInstance(result, tuple)
        self.assertTrue(
            all(isinstance(value, float) for row in result for value in row)
        )

    def test_validate_still_rejects_every_invalid_shape(self):
        for value in (
            None,
            "matrix",
            [[1, 0, 0, 0]] * 3,
            [[1, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 2]],
            (
                (float("inf"), 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            ),
            (
                (float("nan"), 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            ),
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_matrix4(value)

    def test_compose_and_transform_stay_bit_identical(self):
        rng = Random(7)

        for _ in range(200):
            composed = compose_matrix4(
                translation_matrix4(
                    tuple(rng.uniform(-30.0, 30.0) for _ in range(3))
                ),
                rotation_matrix4((0.0, 0.0, rng.uniform(-180.0, 180.0))),
                scale_matrix4(
                    tuple(rng.uniform(0.1, 9.0) for _ in range(3))
                ),
            )
            point = tuple(rng.uniform(-25.0, 25.0) for _ in range(3))

            expected = _reference_validate(composed)
            self.assertEqual(composed, expected)
            self.assertEqual(
                transform_point3(composed, point),
                transform_point3(expected, point),
            )
