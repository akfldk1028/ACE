"""Public-key-only Generation-0 cryptography for Path-B positive intake."""

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


_ROLE_DOMAINS = {
    "legacy_search_impossibility_declaration": (
        "ACE-ICLR2027-LEGACY-SEARCH-IMPOSSIBILITY-VNEXT\x00"
    ),
    "one_thesis_contract": "ACE-ICLR2027-ONE-THESIS-CONTRACT-VNEXT\x00",
    "new_upstream_scientific_snapshot": (
        "ACE-ICLR2027-NEW-UPSTREAM-SCIENTIFIC-SNAPSHOT-VNEXT\x00"
    ),
    "independent_science_migration_review": (
        "ACE-ICLR2027-INDEPENDENT-SCIENCE-MIGRATION-REVIEW-VNEXT\x00"
    ),
    "independent_provenance_migration_review": (
        "ACE-ICLR2027-INDEPENDENT-PROVENANCE-MIGRATION-REVIEW-VNEXT\x00"
    ),
    "independent_security_migration_review": (
        "ACE-ICLR2027-INDEPENDENT-SECURITY-MIGRATION-REVIEW-VNEXT\x00"
    ),
    "provenance_migration_receipt": (
        "ACE-ICLR2027-PROVENANCE-MIGRATION-RECEIPT-VNEXT\x00"
    ),
}

_FIELD_PRIME = (1 << 255) - 19
_CURVE_D = (-121665 * pow(121666, _FIELD_PRIME - 2, _FIELD_PRIME)) % _FIELD_PRIME
_SQRT_MINUS_ONE = pow(2, (_FIELD_PRIME - 1) // 4, _FIELD_PRIME)
_SUBGROUP_ORDER = (1 << 252) + 27742317777372353535851937790883648493


class IntakeCryptoError(ValueError):
    """Raised when public cryptographic material violates the closed contract."""


def _decode_ed25519_point(encoded: bytes) -> tuple[int, int] | None:
    value = int.from_bytes(encoded, "little")
    x_sign = value >> 255
    y = value & ((1 << 255) - 1)
    if y >= _FIELD_PRIME:
        return None

    y_squared = y * y % _FIELD_PRIME
    denominator = (_CURVE_D * y_squared + 1) % _FIELD_PRIME
    if denominator == 0:
        return None
    x_squared = (
        (y_squared - 1)
        * pow(denominator, _FIELD_PRIME - 2, _FIELD_PRIME)
        % _FIELD_PRIME
    )
    x = pow(x_squared, (_FIELD_PRIME + 3) // 8, _FIELD_PRIME)
    if (x * x - x_squared) % _FIELD_PRIME != 0:
        x = x * _SQRT_MINUS_ONE % _FIELD_PRIME
    if (x * x - x_squared) % _FIELD_PRIME != 0:
        return None
    if x == 0 and x_sign == 1:
        return None
    if x & 1 != x_sign:
        x = _FIELD_PRIME - x
    return x, y


def _double_ed25519_point(point: tuple[int, int]) -> tuple[int, int] | None:
    x, y = point
    x_squared = x * x % _FIELD_PRIME
    y_squared = y * y % _FIELD_PRIME
    product = _CURVE_D * x_squared * y_squared % _FIELD_PRIME
    x_denominator = (1 + product) % _FIELD_PRIME
    y_denominator = (1 - product) % _FIELD_PRIME
    if x_denominator == 0 or y_denominator == 0:
        return None
    doubled_x = (
        2
        * x
        * y
        * pow(x_denominator, _FIELD_PRIME - 2, _FIELD_PRIME)
        % _FIELD_PRIME
    )
    doubled_y = (
        (y_squared + x_squared)
        * pow(y_denominator, _FIELD_PRIME - 2, _FIELD_PRIME)
        % _FIELD_PRIME
    )
    return doubled_x, doubled_y


def _is_canonical_nonsmall_order_point(encoded: bytes) -> bool:
    point = _decode_ed25519_point(encoded)
    if point is None:
        return False
    for _ in range(3):
        point = _double_ed25519_point(point)
        if point is None:
            return False
    return point != (0, 1)


def artifact_signature_message(role: str, artifact_bytes: bytes) -> bytes:
    """Return the exact role-domain prefix followed by canonical artifact bytes."""

    if type(role) is not str or role not in _ROLE_DOMAINS:
        raise IntakeCryptoError("invalid_artifact_role")
    if (
        type(artifact_bytes) is not bytes
        or not artifact_bytes
        or not artifact_bytes.endswith(b"\n")
        or b"\r" in artifact_bytes
        or b"\n" in artifact_bytes[:-1]
    ):
        raise IntakeCryptoError("invalid_artifact_bytes")
    return _ROLE_DOMAINS[role].encode("ascii") + artifact_bytes


def verify_ed25519(public_key: bytes, signature: bytes, message: bytes) -> None:
    """Verify an Ed25519 signature with public material only."""

    if (
        type(public_key) is not bytes
        or type(signature) is not bytes
        or type(message) is not bytes
    ):
        raise IntakeCryptoError("invalid_ed25519_type")
    if len(public_key) != 32 or len(signature) != 64:
        raise IntakeCryptoError("invalid_ed25519_length")
    if not _is_canonical_nonsmall_order_point(public_key):
        raise IntakeCryptoError("invalid_ed25519_point")
    if not _is_canonical_nonsmall_order_point(signature[:32]):
        raise IntakeCryptoError("invalid_ed25519_point")
    if int.from_bytes(signature[32:], "little") >= _SUBGROUP_ORDER:
        raise IntakeCryptoError("invalid_ed25519_scalar")
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
    except (ValueError, InvalidSignature) as exc:
        raise IntakeCryptoError("cryptographic_signature_failed") from exc
