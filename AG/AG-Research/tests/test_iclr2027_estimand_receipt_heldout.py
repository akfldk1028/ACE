import copy
import hashlib
import json
import math
import re
import unittest
from collections import Counter
from pathlib import Path

from iclr2027.estimand_receipt_evaluators import evaluate_frozen_artifacts
from iclr2027.estimand_receipt_generator import generate_clean_benchmark
from iclr2027.estimand_receipts import ObservedArtifactV1


PACK_PATH = (
    Path(__file__).resolve().parents[2]
    / ".superpowers"
    / "sdd"
    / "2026-09-01-iclr2027-estimand-receipt-study"
    / "held-out-fault-pack.json"
)

INTERFACE_HASHES = {
    "evaluator": "2bcdf8380b8310b39146159821f851128e30fdffbea0a0b33aa6409e7e129480",
    "generator": "3fa115d861c578ad8e7ba422b9841b2938434e4721dc2a59390934de582c8307",
    "oracle": "264a1186415030cada20239231b28bedc4022f916508c3a65e1b159e592519d2",
    "receipt": "af001d34fc6e558b0ae1e48b3fbc2601d1e7e22099c1d2f88b8d094240535879",
}

ARTIFACT_KEYS = {
    "schema_version",
    "study_id",
    "unit_id",
    "site_id",
    "stratum_id",
    "assignment",
    "requested_action_id",
    "requested_members",
    "executed_action_id",
    "executed_members",
    "target_binding_sha256",
    "terminal_owner_id",
    "terminal_value_sha256",
    "scorer_weights",
    "protocol_version",
    "policy_record",
    "bound_certificate_ids",
    "payload_sha256",
}

ESTIMANDS = ("tau_itt", "tau_cb", "psi_natural")
FAMILY_BLOCKS = {
    "E": frozenset({"tau_cb"}),
    "B": frozenset(ESTIMANDS),
    "T": frozenset(ESTIMANDS),
    "S": frozenset(ESTIMANDS),
    "G": frozenset(ESTIMANDS),
    "P": frozenset({"psi_natural"}),
}
FAMILY_FIELDS = {
    "E": frozenset({"executed_action_id", "executed_members"}),
    "B": frozenset({"target_binding_sha256"}),
    "T": frozenset({"terminal_owner_id", "terminal_value_sha256"}),
    "S": frozenset({"scorer_weights"}),
    "G": frozenset({"protocol_version"}),
    "P": frozenset({"policy_record"}),
}

# This is the closed operation grammar. Every operation is interpreted below;
# the value records the only receipt family whose fields it may edit.
OP_FAMILY = {
    "e_replace_action": "E",
    "e_replace_members": "E",
    "e_reconstruct": "E",
    "e_append_member": "E",
    "e_replace_action_and_members": "E",
    "b_replace_target": "B",
    "b_use_committed_allowed_target": "B",
    "t_replace_owner": "T",
    "t_replace_value": "T",
    "t_reconstruct": "T",
    "t_replace_both": "T",
    "s_replace_first_key": "S",
    "s_replace_all_keys": "S",
    "s_add_zero_weight": "S",
    "s_replace_indexed_keys": "S",
    "g_replace_protocol": "G",
    "g_use_committed_allowed_protocol": "G",
    "p_replace_snapshot": "P",
    "p_replace_event": "P",
    "p_reconstruct": "P",
    "p_halve_propensity": "P",
    "p_replace_policy_id": "P",
}
OPS_WITHOUT_SALT = {
    "e_reconstruct",
    "b_use_committed_allowed_target",
    "t_reconstruct",
    "g_use_committed_allowed_protocol",
    "p_reconstruct",
    "p_halve_propensity",
}


def _canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _round_trip(value):
    return json.loads(_canonical(value).decode("utf-8"))


def _load_pack():
    return json.loads(PACK_PATH.read_text(encoding="utf-8"))


def _replacement_digest(artifact, salt):
    return _digest(
        {
            "base_payload_sha256": artifact["payload_sha256"],
            "salt": salt,
            "schema_version": "heldout-replacement/v1",
        }
    )


def _opaque_id(prefix, artifact, salt):
    return prefix + "-" + _replacement_digest(artifact, salt)[:24]


def _unique_score_key(artifact, salt, occupied):
    nonce = 0
    while True:
        candidate = _opaque_id("score-key", artifact, f"{salt}:{nonce}")
        if candidate not in occupied:
            return candidate
        nonce += 1


def _replace_members(artifact, salt, append):
    members = _round_trip(artifact["executed_members"])
    if not isinstance(members, list):
        raise AssertionError("executed_members must serialize as a list")
    token = _opaque_id("member", artifact, salt)
    if append or not members:
        members.append(token)
    else:
        members[0] = token
    artifact["executed_members"] = sorted(set(members))


def _replace_score_keys(artifact, salt, replace_all):
    rows = _round_trip(artifact["scorer_weights"])
    if not rows:
        raise AssertionError("scorer_weights must be nonempty")
    indexes = range(len(rows)) if replace_all else range(1)
    occupied = {row["key"] for row in rows}
    for index in indexes:
        occupied.discard(rows[index]["key"])
        new_key = _unique_score_key(artifact, f"{salt}:{index}", occupied)
        rows[index]["key"] = new_key
        occupied.add(new_key)
    artifact["scorer_weights"] = sorted(rows, key=lambda row: row["key"])


def _apply_operation(artifact, original, commitment, operation):
    op = operation["op"]
    salt = operation.get("salt")

    if op == "e_replace_action":
        artifact["executed_action_id"] = _opaque_id("action", artifact, salt)
    elif op == "e_replace_members":
        _replace_members(artifact, salt, append=False)
    elif op == "e_reconstruct":
        artifact["executed_action_id"] = _round_trip(original["executed_action_id"])
        artifact["executed_members"] = _round_trip(original["executed_members"])
    elif op == "e_append_member":
        _replace_members(artifact, salt, append=True)
    elif op == "e_replace_action_and_members":
        artifact["executed_action_id"] = _opaque_id(
            "action", artifact, salt + ":action"
        )
        _replace_members(artifact, salt + ":members", append=False)
    elif op == "b_replace_target":
        artifact["target_binding_sha256"] = _replacement_digest(artifact, salt)
    elif op == "b_use_committed_allowed_target":
        allowed = commitment["allowed_target_binding_sha256"]
        if not isinstance(allowed, list) or len(allowed) != 1:
            raise AssertionError("B control requires exactly one allowed target")
        if allowed[0] == original["target_binding_sha256"]:
            raise AssertionError("B control allowed target must differ from primary")
        artifact["target_binding_sha256"] = allowed[0]
    elif op == "t_replace_owner":
        artifact["terminal_owner_id"] = _opaque_id("owner", artifact, salt)
    elif op == "t_replace_value":
        artifact["terminal_value_sha256"] = _replacement_digest(artifact, salt)
    elif op == "t_reconstruct":
        artifact["terminal_owner_id"] = _round_trip(original["terminal_owner_id"])
        artifact["terminal_value_sha256"] = original["terminal_value_sha256"]
    elif op == "t_replace_both":
        artifact["terminal_owner_id"] = _opaque_id(
            "owner", artifact, salt + ":owner"
        )
        artifact["terminal_value_sha256"] = _replacement_digest(
            artifact, salt + ":value"
        )
    elif op == "s_replace_first_key":
        _replace_score_keys(artifact, salt, replace_all=False)
    elif op in {"s_replace_all_keys", "s_replace_indexed_keys"}:
        _replace_score_keys(artifact, salt, replace_all=True)
    elif op == "s_add_zero_weight":
        rows = _round_trip(artifact["scorer_weights"])
        occupied = {row["key"] for row in rows}
        rows.append(
            {
                "schema_version": "score-weight/v1",
                "key": _unique_score_key(artifact, salt, occupied),
                "weight": 0.0,
            }
        )
        artifact["scorer_weights"] = sorted(rows, key=lambda row: row["key"])
    elif op == "g_replace_protocol":
        artifact["protocol_version"] = _opaque_id("protocol", artifact, salt)
    elif op == "g_use_committed_allowed_protocol":
        allowed = commitment["allowed_protocol_versions"]
        if not isinstance(allowed, list) or len(allowed) != 1:
            raise AssertionError("G control requires exactly one allowed protocol")
        if allowed[0] == original["protocol_version"]:
            raise AssertionError("G control allowed protocol must differ from primary")
        artifact["protocol_version"] = _round_trip(allowed[0])
    elif op == "p_replace_snapshot":
        artifact["policy_record"]["information_snapshot_sha256"] = (
            _replacement_digest(artifact, salt)
        )
    elif op == "p_replace_event":
        artifact["policy_record"]["decision_event_sha256"] = _replacement_digest(
            artifact, salt
        )
    elif op == "p_reconstruct":
        artifact["policy_record"] = _round_trip(original["policy_record"])
    elif op == "p_halve_propensity":
        propensity = artifact["policy_record"]["propensity"] * 0.5
        if not math.isfinite(propensity) or not 0.0 < propensity <= 1.0:
            raise AssertionError("halved propensity must remain schema-valid")
        artifact["policy_record"]["propensity"] = propensity
    elif op == "p_replace_policy_id":
        artifact["policy_record"]["policy_id"] = _opaque_id(
            "policy", artifact, salt
        )
    else:
        raise AssertionError(f"operation outside closed grammar: {op}")


def _reseal(artifact):
    unsigned = {key: value for key, value in artifact.items() if key != "payload_sha256"}
    artifact["payload_sha256"] = _digest(unsigned)
    return artifact


def _apply_case(source, case, commitment):
    original = _round_trip(source)
    artifact = _round_trip(source)
    for operation in case["operations"]:
        _apply_operation(artifact, original, commitment, operation)
    return _reseal(artifact)


def _blocked_estimands(case):
    if case["case_kind"] == "invariance_control":
        return frozenset()
    blocked = set()
    for family in case["families"]:
        blocked.update(FAMILY_BLOCKS[family])
    return frozenset(blocked)


def _artifact_dict(value):
    if isinstance(value, dict):
        return _round_trip(value)
    return _round_trip(value.to_dict())


def _walk_mappings(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_mappings(child)


def _scalar_strings(value):
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        result = set()
        for child in value.values():
            result.update(_scalar_strings(child))
        return result
    if isinstance(value, list):
        result = set()
        for child in value:
            result.update(_scalar_strings(child))
        return result
    return set()


def _commitment_candidates(trust_root):
    candidates = [
        value
        for value in _walk_mappings(trust_root)
        if "allowed_target_binding_sha256" in value
        and "allowed_protocol_versions" in value
    ]
    if not candidates:
        raise AssertionError("trust root contains no estimand commitments")
    return candidates


def _corresponding_commitment(candidates, source, unit_ordinal, artifact_count):
    if len(candidates) == 1:
        return candidates[0]

    identity_values = {
        source[key]
        for key in ("study_id", "unit_id", "site_id", "stratum_id", "payload_sha256")
        if isinstance(source[key], str)
    }
    scored = [
        (len(identity_values & _scalar_strings(candidate)), candidate)
        for candidate in candidates
    ]
    best_score = max(score for score, _ in scored)
    winners = [candidate for score, candidate in scored if score == best_score]
    if best_score > 0 and len(winners) == 1:
        return winners[0]
    if len(candidates) == artifact_count:
        return candidates[unit_ordinal]
    raise AssertionError("corresponding estimand commitment is not unique")


def _build_public_rows(pack):
    clean = generate_clean_benchmark()
    if len(clean.artifacts) < 24:
        raise AssertionError("clean benchmark must expose at least 24 artifacts")

    trust_root = clean.trust_root.to_dict()
    commitments = _commitment_candidates(trust_root)
    public_rows = []
    expected = {}
    for public_ordinal, case in enumerate(pack["cases"]):
        source = _artifact_dict(clean.artifacts[case["unit_ordinal"]])
        commitment = _corresponding_commitment(
            commitments, source, case["unit_ordinal"], len(clean.artifacts)
        )
        artifact = _apply_case(source, case, commitment)
        anonymous_sha = _digest(
            {
                "artifact_payload_sha256": artifact["payload_sha256"],
                "public_ordinal": public_ordinal,
            }
        )
        public_rows.append(
            _canonical(
                {
                    "artifact": artifact,
                    "case_id": anonymous_sha,
                    "schema_version": "public-artifact-row/v1",
                }
            )
        )
        blocked = _blocked_estimands(case)
        for estimand in ESTIMANDS:
            expected[(anonymous_sha, estimand)] = (
                "blocked" if estimand in blocked else "certified"
            )

    trust_root_bytes = _canonical(trust_root)
    return tuple(public_rows), trust_root_bytes, expected


class HeldOutEstimandReceiptTest(unittest.TestCase):
    def test_pack_is_canonical_and_self_sealed(self):
        raw = PACK_PATH.read_bytes()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertNotIn(b"\r", raw)
        document = json.loads(raw.decode("utf-8"))
        self.assertEqual(raw, _canonical(document) + b"\n")
        self.assertEqual(
            set(document),
            {"schema_version", "interface_hashes", "cases", "payload_sha256"},
        )
        self.assertEqual(document["schema_version"], "estimand-heldout-fault-pack/v1")
        self.assertEqual(document["interface_hashes"], INTERFACE_HASHES)
        unsigned = {
            key: document[key]
            for key in ("schema_version", "interface_hashes", "cases")
        }
        self.assertEqual(document["payload_sha256"], _digest(unsigned))
        self.assertIsNone(re.search(rb"\d{19}", raw))

    def test_case_census_and_closed_grammar(self):
        cases = _load_pack()["cases"]
        self.assertEqual(len(cases), 24)
        self.assertEqual(
            [case["case_id"] for case in cases],
            [f"heldout-case-{index:02d}" for index in range(24)],
        )
        self.assertEqual([case["unit_ordinal"] for case in cases], list(range(24)))
        for case in cases:
            self.assertEqual(
                set(case),
                {"case_id", "unit_ordinal", "case_kind", "families", "operations"},
            )
            self.assertTrue(case["operations"])
            for operation in case["operations"]:
                op = operation["op"]
                self.assertIn(op, OP_FAMILY)
                self.assertIn(OP_FAMILY[op], case["families"])
                expected_keys = {"op"} if op in OPS_WITHOUT_SALT else {"op", "salt"}
                self.assertEqual(set(operation), expected_keys)

        singles = Counter(
            case["families"][0]
            for case in cases
            if case["case_kind"] == "harmful_single"
        )
        controls = Counter(
            case["families"][0]
            for case in cases
            if case["case_kind"] == "invariance_control"
        )
        compounds = [
            tuple(case["families"])
            for case in cases
            if case["case_kind"] == "harmful_compound"
        ]
        self.assertEqual(singles, Counter({family: 2 for family in "EBTSGP"}))
        self.assertEqual(controls, Counter({family: 1 for family in "EBTSGP"}))
        self.assertEqual(
            compounds,
            [("E", "B"), ("B", "T"), ("T", "S"), ("S", "G"), ("G", "P"), ("P", "E")],
        )

    def test_mutations_are_scoped_schema_valid_and_resealed(self):
        pack = _load_pack()
        clean = generate_clean_benchmark()
        self.assertGreaterEqual(len(clean.artifacts), 24)
        commitments = _commitment_candidates(clean.trust_root.to_dict())
        for case in pack["cases"]:
            source = _artifact_dict(clean.artifacts[case["unit_ordinal"]])
            self.assertEqual(set(source), ARTIFACT_KEYS)
            commitment = _corresponding_commitment(
                commitments, source, case["unit_ordinal"], len(clean.artifacts)
            )
            artifact = _apply_case(source, case, commitment)
            allowed = {"payload_sha256"}
            for family in case["families"]:
                allowed.update(FAMILY_FIELDS[family])
            changed = {
                key for key in ARTIFACT_KEYS if source[key] != artifact[key]
            }
            self.assertLessEqual(changed, allowed)
            unsigned = {
                key: value
                for key, value in artifact.items()
                if key != "payload_sha256"
            }
            self.assertEqual(artifact["payload_sha256"], _digest(unsigned))
            ObservedArtifactV1.from_dict(_round_trip(artifact))

            if case["case_kind"] == "harmful_single":
                self.assertTrue(changed & FAMILY_FIELDS[case["families"][0]])
            elif case["case_kind"] == "harmful_compound":
                for family in case["families"]:
                    self.assertTrue(changed & FAMILY_FIELDS[family])
            elif case["families"] == ["B"]:
                self.assertEqual(changed, {"target_binding_sha256", "payload_sha256"})
                self.assertEqual(
                    artifact["target_binding_sha256"],
                    commitment["allowed_target_binding_sha256"][0],
                )
                self.assertNotEqual(
                    artifact["target_binding_sha256"], source["target_binding_sha256"]
                )
            elif case["families"] == ["S"]:
                self.assertEqual(changed, {"scorer_weights", "payload_sha256"})
                added = [
                    row
                    for row in artifact["scorer_weights"]
                    if row not in source["scorer_weights"]
                ]
                self.assertEqual(len(added), 1)
                self.assertEqual(added[0]["weight"], 0.0)
            elif case["families"] == ["G"]:
                self.assertEqual(changed, {"protocol_version", "payload_sha256"})
                self.assertEqual(
                    artifact["protocol_version"],
                    commitment["allowed_protocol_versions"][0],
                )
                self.assertNotEqual(
                    artifact["protocol_version"], source["protocol_version"]
                )
            else:
                self.assertFalse(changed)

    def test_public_rows_are_anonymous_and_private_label_free(self):
        pack = _load_pack()
        public_rows, _, _ = _build_public_rows(pack)
        forbidden = {
            b"harmful",
            b"control",
            b"compound",
            b"certified",
            b"blocked",
            b'"families"',
        }
        forbidden.update(case["case_id"].encode("utf-8") for case in pack["cases"])
        forbidden.update((f'"{family}"').encode("ascii") for family in FAMILY_BLOCKS)
        for row in public_rows:
            for token in forbidden:
                self.assertNotIn(token, row)
            parsed = json.loads(row.decode("utf-8"))
            self.assertEqual(row, _canonical(parsed))
            self.assertRegex(parsed["case_id"], r"^[0-9a-f]{64}$")

    def test_full_estimand_gate_lattice(self):
        pack = _load_pack()
        public_rows, trust_root_bytes, expected = _build_public_rows(pack)
        rows = evaluate_frozen_artifacts(public_rows, trust_root_bytes)
        actual = {}
        for row in rows:
            if row.configuration != "full_estimand_gate":
                continue
            key = (row.public_case_id, row.estimand)
            self.assertNotIn(key, actual)
            actual[key] = row.status
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
