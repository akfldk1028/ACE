import hashlib
import json
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from shapely.geometry import box

from design.maas.book_language.agent_authored_supply import (
    AGENT_AUTHORED_BOOK_PATH_MANIFEST_SCHEMA,
    AGENT_AUTHORED_CAUSAL_BOOK_PATH_MANIFEST_SCHEMA,
    AGENT_AUTHORED_OFFER_BOUND_MANIFEST_SCHEMA,
    AgentAuthoredAdmission,
    AgentAuthoredSupplyError,
    build_agent_authored_program_seeds,
    filter_agent_authored_replay_programs,
    is_validated_codex_oauth_candidate,
    is_validated_codex_oauth_program_payload,
    load_agent_authored_geometry_programs,
)
from design.maas.book_language.candidate_analysis import _llm_authored_candidate
from design.maas.book_language.portfolio_benchmark import (
    _bind_trusted_codex_completion,
    _trusted_codex_selection_pool,
    run_book_program_portfolios,
)
from design.management.commands.benchmark_maas_book_program_portfolios import (
    Command,
)
from design.maas.geometry_language import (
    GeometryProgram,
    compile_geometry_program,
    geometry_programs_from_author_payload,
)


CODEX_PROVIDER = "codex_oauth_llm_geometry_author"


def _number(name: str, value: float) -> dict:
    return {
        "name": name,
        "value_type": "number",
        "numeric_value": value,
    }


def _valid_program_item() -> dict:
    return {
        "name": "codex_offset_court",
        "base_seed": "block",
        "intent_tags": ["courtyard", "offset"],
        "root_id": "court",
        "nodes": [
            {
                "id": "seed",
                "kind": "primitive",
                "operator": "box",
                "inputs": [],
                "parameters": [
                    _number("width", 1.0),
                    _number("depth", 1.0),
                    _number("height", 1.0),
                ],
                "semantic_role": "base_seed",
            },
            {
                "id": "court",
                "kind": "macro",
                "operator": "courtyard",
                "inputs": ["seed"],
                "parameters": [
                    _number("margin_ratio", 0.24),
                    {
                        "name": "open_side",
                        "value_type": "string",
                        "string_value": "west",
                    },
                ],
                "semantic_role": "public_threshold",
            },
        ],
    }


def _manifest(programs: list[dict]) -> dict:
    return {
        "schema_version": "arr.maas.codex_oauth_geometry_manifest.v1",
        "provider": CODEX_PROVIDER,
        "authoring_session_id": "codex-session-20260805",
        "request_id": "task-4-request-001",
        "programs": programs,
    }


def _write_manifest(directory: str, payload: dict) -> tuple[Path, bytes]:
    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    path = Path(directory) / "agent-authored-programs.json"
    path.write_bytes(raw)
    return path, raw


def _admission(
    raw: bytes,
    *,
    session_id: str = "codex-session-20260805",
    request_id: str = "task-4-request-001",
    program_hashes: tuple[str, ...] | None = None,
) -> AgentAuthoredAdmission:
    if program_hashes is None:
        payload = json.loads(raw.decode("utf-8"))
        program_hashes = tuple(
            program.program_hash()
            for program in geometry_programs_from_author_payload(
                {"programs": payload["programs"]},
                expected_count=len(payload["programs"]),
            )
        )
    return AgentAuthoredAdmission(
        authoring_session_id=session_id,
        request_id=request_id,
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
        admitted_program_hashes=program_hashes,
    )


def _candidate(program_payload: dict) -> SimpleNamespace:
    return SimpleNamespace(
        source=SimpleNamespace(
            metadata={"authored_geometry_program": program_payload}
        )
    )


class AgentAuthoredSupplyTests(TestCase):
    def test_replay_filter_keeps_only_requested_validated_programs(self):
        hashes = ("1" * 64, "2" * 64, "3" * 64)
        programs = tuple(
            SimpleNamespace(program_hash=lambda value=value: value)
            for value in hashes
        )

        selected = filter_agent_authored_replay_programs(
            programs,
            (hashes[2], hashes[0]),
        )

        self.assertEqual(
            tuple(program.program_hash() for program in selected),
            (hashes[0], hashes[2]),
        )
        with self.assertRaisesRegex(
            AgentAuthoredSupplyError,
            "replay program hash is not in the validated manifest",
        ):
            filter_agent_authored_replay_programs(programs, ("f" * 64,))

    def test_v4_codex_manifest_rejects_selected_path_outside_persisted_offer(self):
        from design.maas.book_language.composition_lattice import (
            iter_book_composition_paths,
        )

        item = _valid_program_item()
        paths = tuple(iter_book_composition_paths())
        selected_path_id = paths[0].path_id
        offered_path_ids = [paths[1].path_id]
        offered_hash = hashlib.sha256(json.dumps(
            offered_path_ids,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        response = {
            "schema_version": (
                "arr.maas.codex_oauth_author_response."
                "v2_offered_path_membership"
            ),
            "response_id": "codex-response-20260806-v8",
            "selected_bindings": [{
                "program_name": item["name"],
                "book_composition_path_id": selected_path_id,
                "offered_book_composition_path_ids": offered_path_ids,
                "offered_path_ids_sha256": offered_hash,
                "prompt_sha256": "a" * 64,
                "direct_llm_response_id": "direct-response-invalid-offer",
            }],
        }
        response_hash = hashlib.sha256(json.dumps(
            response,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        response["response_sha256"] = response_hash
        item.update({
            "book_composition_path_id": selected_path_id,
            "execution_contract": {
                "schema_version": (
                    "arr.maas.codex_book_path_execution_binding.v1"
                ),
                "book_composition_path_id": selected_path_id,
                "author_response_sha256": response_hash,
            },
        })
        manifest = {
            **_manifest([item]),
            "schema_version": AGENT_AUTHORED_OFFER_BOUND_MANIFEST_SCHEMA,
            "oauth_author_response": response,
        }
        parsed = geometry_programs_from_author_payload(
            {"programs": [item]},
            expected_count=1,
        )[0]
        bound_hash = replace(
            parsed,
            execution_contract=item["execution_contract"],
        ).program_hash()

        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(directory, manifest)
            with self.assertRaisesRegex(
                AgentAuthoredSupplyError,
                "not in persisted LLM offer",
            ):
                load_agent_authored_geometry_programs(
                    path,
                    admission=_admission(
                        raw,
                        program_hashes=(bound_hash,),
                    ),
                )

            response["selected_bindings"][0][
                "offered_book_composition_path_ids"
            ] = [selected_path_id]
            response["selected_bindings"][0][
                "offered_path_ids_sha256"
            ] = hashlib.sha256(
                json.dumps(
                    [selected_path_id],
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            response.pop("response_sha256")
            response_hash = hashlib.sha256(json.dumps(
                response,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")).hexdigest()
            response["response_sha256"] = response_hash
            item["execution_contract"][
                "author_response_sha256"
            ] = response_hash
            valid_manifest = {
                **_manifest([item]),
                "schema_version": AGENT_AUTHORED_OFFER_BOUND_MANIFEST_SCHEMA,
                "oauth_author_response": response,
            }
            parsed = geometry_programs_from_author_payload(
                {"programs": [item]},
                expected_count=1,
            )[0]
            valid_bound_hash = replace(
                parsed,
                execution_contract=item["execution_contract"],
            ).program_hash()
            valid_path, valid_raw = _write_manifest(
                directory,
                valid_manifest,
            )
            programs = load_agent_authored_geometry_programs(
                valid_path,
                admission=_admission(
                    valid_raw,
                    program_hashes=(valid_bound_hash,),
                ),
            )

        self.assertEqual(programs[0].program_hash(), valid_bound_hash)

    def test_v3_codex_manifest_binds_book_path_and_response_into_program_hash(self):
        from design.maas.book_language.composition_lattice import (
            iter_book_composition_paths,
        )

        item = _valid_program_item()
        path_id = next(iter_book_composition_paths()).path_id
        response = {
            "schema_version": "arr.maas.codex_oauth_author_response.v1",
            "response_id": "codex-response-20260806-v7",
            "selected_bindings": [{
                "program_name": item["name"],
                "book_composition_path_id": path_id,
            }],
        }
        response_hash = hashlib.sha256(json.dumps(
            response,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        response["response_sha256"] = response_hash
        item.update({
            "book_composition_path_id": path_id,
            "execution_contract": {
                "schema_version": (
                    "arr.maas.codex_book_path_execution_binding.v1"
                ),
                "book_composition_path_id": path_id,
                "author_response_sha256": response_hash,
            },
        })
        manifest = {
            **_manifest([item]),
            "schema_version": (
                AGENT_AUTHORED_CAUSAL_BOOK_PATH_MANIFEST_SCHEMA
            ),
            "oauth_author_response": response,
        }
        parsed = geometry_programs_from_author_payload(
            {"programs": [item]},
            expected_count=1,
        )[0]
        bound_hash = replace(
            parsed,
            execution_contract=item["execution_contract"],
        ).program_hash()

        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(directory, manifest)
            programs = load_agent_authored_geometry_programs(
                path,
                admission=_admission(
                    raw,
                    program_hashes=(bound_hash,),
                ),
            )
            tampered = json.loads(raw.decode("utf-8"))
            tampered["programs"][0]["execution_contract"][
                "author_response_sha256"
            ] = "f" * 64
            tampered_path, tampered_raw = _write_manifest(
                directory,
                tampered,
            )
            with self.assertRaisesRegex(
                AgentAuthoredSupplyError,
                "causal BOOK composition binding",
            ):
                load_agent_authored_geometry_programs(
                    tampered_path,
                    admission=_admission(
                        tampered_raw,
                        program_hashes=(bound_hash,),
                    ),
                )

        self.assertEqual(programs[0].program_hash(), bound_hash)
        self.assertEqual(
            programs[0].execution_contract[
                "book_composition_path_id"
            ],
            path_id,
        )

    def test_v3_distinct_programs_may_reuse_one_book_path(self):
        """A BOOK operation is a reusable language rule, not a portfolio ID."""

        from design.maas.book_language.composition_lattice import (
            iter_book_composition_paths,
        )

        path_id = next(iter_book_composition_paths()).path_id
        first = _valid_program_item()
        second = json.loads(json.dumps(first))
        second["name"] = "codex_offset_court_deeper"
        second["nodes"][1]["parameters"][0]["numeric_value"] = 0.31
        items = [first, second]
        response = {
            "schema_version": "arr.maas.codex_oauth_author_response.v1",
            "response_id": "codex-response-shared-book-language",
            "selected_bindings": [
                {
                    "program_name": item["name"],
                    "book_composition_path_id": path_id,
                }
                for item in items
            ],
        }
        response_hash = hashlib.sha256(json.dumps(
            response,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        response["response_sha256"] = response_hash
        for item in items:
            item["book_composition_path_id"] = path_id
            item["execution_contract"] = {
                "schema_version": (
                    "arr.maas.codex_book_path_execution_binding.v1"
                ),
                "book_composition_path_id": path_id,
                "author_response_sha256": response_hash,
            }
        manifest = {
            **_manifest(items),
            "schema_version": AGENT_AUTHORED_CAUSAL_BOOK_PATH_MANIFEST_SCHEMA,
            "oauth_author_response": response,
        }
        parsed = geometry_programs_from_author_payload(
            {"programs": items},
            expected_count=2,
        )
        bound_hashes = tuple(
            replace(
                program,
                execution_contract=item["execution_contract"],
            ).program_hash()
            for program, item in zip(parsed, items)
        )

        with TemporaryDirectory() as directory:
            manifest_path, raw = _write_manifest(directory, manifest)
            programs = load_agent_authored_geometry_programs(
                manifest_path,
                admission=_admission(raw, program_hashes=bound_hashes),
            )

        self.assertEqual(len(programs), 2)
        self.assertEqual(
            {
                program.metadata["book_composition_path_id"]
                for program in programs
            },
            {path_id},
        )

    def test_v2_codex_manifest_requires_and_preserves_book_paths(self):
        from design.maas.book_language.composition_lattice import (
            iter_book_composition_paths,
        )

        item = _valid_program_item()
        path_id = next(iter_book_composition_paths()).path_id
        manifest = {
            **_manifest([item]),
            "schema_version": AGENT_AUTHORED_BOOK_PATH_MANIFEST_SCHEMA,
        }
        with TemporaryDirectory() as directory:
            missing_path, missing_raw = _write_manifest(directory, manifest)
            with self.assertRaisesRegex(
                AgentAuthoredSupplyError,
                "BOOK composition path binding",
            ):
                load_agent_authored_geometry_programs(
                    missing_path,
                    admission=_admission(missing_raw),
                )

            manifest["programs"][0]["book_composition_path_id"] = path_id
            valid_path, valid_raw = _write_manifest(directory, manifest)
            programs = load_agent_authored_geometry_programs(
                valid_path,
                admission=_admission(valid_raw),
            )

        self.assertEqual(
            programs[0].metadata["book_composition_path_id"],
            path_id,
        )
        self.assertEqual(
            programs[0].metadata["author_manifest_schema_version"],
            AGENT_AUTHORED_BOOK_PATH_MANIFEST_SCHEMA,
        )

    def test_codex_lineage_failure_is_persisted_inside_completion(self):
        completion = _bind_trusted_codex_completion(
            {"hard_pass": True, "failures": []},
            manifest_required=True,
            selected_count=2,
            trusted_codex_selected_count=1,
        )
        self.assertFalse(completion["hard_pass"])
        self.assertIn(
            "selected_codex_oauth_lineage_incomplete",
            completion["failures"],
        )
        self.assertEqual(completion["trusted_codex_selected_count"], 1)

    def test_management_command_accepts_agent_authored_manifest_path(self):
        parser = Command().create_parser(
            "manage.py",
            "benchmark_maas_book_program_portfolios",
        )
        options = vars(parser.parse_args([
            "--agent-authored-manifest",
            "codex-programs.json",
        ]))
        self.assertEqual(
            options["agent_authored_manifest"],
            "codex-programs.json",
        )

    def test_runtime_manifest_option_fails_before_any_paid_author_request(self):
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(
                directory,
                {**_manifest([_valid_program_item()]), "provider": "forged"},
            )
            with patch(
                "design.maas.book_language.candidate_generation.author_geometry_programs_with_openai",
                side_effect=AssertionError("paid author must not be called"),
            ), self.assertRaises(AgentAuthoredSupplyError):
                run_book_program_portfolios(
                    box(0.0, 0.0, 40.0, 30.0),
                    pnu="test-pnu",
                    output_dir=Path(directory) / "output",
                    program_slugs=("neighborhood",),
                    agent_authored_manifest_path=path,
                    agent_authored_admission=_admission(raw),
                )

    def test_runtime_manifest_requires_a_trusted_admission_contract(self):
        with TemporaryDirectory() as directory:
            path, _ = _write_manifest(
                directory,
                _manifest([_valid_program_item()]),
            )
            with self.assertRaisesRegex(
                AgentAuthoredSupplyError,
                "trusted admission contract",
            ):
                run_book_program_portfolios(
                    box(0.0, 0.0, 40.0, 30.0),
                    pnu="test-pnu",
                    output_dir=Path(directory) / "output",
                    program_slugs=("neighborhood",),
                    agent_authored_manifest_path=path,
                )

    def test_manifest_identity_and_hashes_must_match_trusted_admission(self):
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(
                directory,
                _manifest([_valid_program_item()]),
            )
            valid = _admission(raw)
            cases = (
                replace(valid, authoring_session_id="other-session"),
                replace(valid, request_id="other-request"),
                replace(valid, manifest_sha256="f" * 64),
                replace(
                    valid,
                    admitted_program_hashes=frozenset({"e" * 64}),
                ),
            )
            for admission in cases:
                with self.subTest(admission=admission), self.assertRaises(
                    AgentAuthoredSupplyError
                ):
                    load_agent_authored_geometry_programs(
                        path,
                        admission=admission,
                    )

    def test_procedural_program_identity_cannot_be_relabelled_as_codex_oauth(self):
        item = _valid_program_item()
        item["metadata"] = {
            "author_provider": "bounded_procedural_geometry_agent",
            "llm_geometry_author_active": False,
        }
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(directory, _manifest([item]))
            with self.assertRaisesRegex(
                AgentAuthoredSupplyError,
                "procedural authorship",
            ):
                load_agent_authored_geometry_programs(
                    path,
                    admission=_admission(raw),
                )

    def test_invalid_ast_node_fails_the_whole_manifest_closed(self):
        invalid = _valid_program_item()
        invalid["nodes"][1]["operator"] = "unregistered_finished_mesh"
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(
                directory,
                _manifest([_valid_program_item(), invalid]),
            )
            with self.assertRaises(AgentAuthoredSupplyError):
                load_agent_authored_geometry_programs(
                    path,
                    admission=_admission(
                        raw,
                        program_hashes=("a" * 64, "b" * 64),
                    ),
                )

    def test_completed_mesh_payload_is_not_accepted_as_typed_authorship(self):
        item = _valid_program_item()
        item["mesh"] = {
            "vertices": [[0.0, 0.0, 0.0]],
            "triangles": [],
        }
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(directory, _manifest([item]))
            with self.assertRaisesRegex(
                AgentAuthoredSupplyError,
                "mesh or parcel-coordinate payload",
            ):
                load_agent_authored_geometry_programs(
                    path,
                    admission=_admission(
                        raw,
                        program_hashes=("a" * 64,),
                    ),
                )

    def test_valid_manifest_preserves_provider_session_request_and_hashes(self):
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(
                directory,
                _manifest([_valid_program_item()]),
            )
            admission = _admission(raw)
            programs = load_agent_authored_geometry_programs(
                path,
                admission=admission,
            )

        self.assertEqual(len(programs), 1)
        program = programs[0]
        metadata = program.metadata
        self.assertEqual(metadata["author_provider"], CODEX_PROVIDER)
        self.assertEqual(
            metadata["authoring_session_id"],
            "codex-session-20260805",
        )
        self.assertEqual(metadata["author_request_id"], "task-4-request-001")
        self.assertEqual(
            metadata["author_manifest_sha256"],
            hashlib.sha256(raw).hexdigest(),
        )
        self.assertEqual(metadata["author_program_hash"], program.program_hash())
        self.assertTrue(metadata["llm_geometry_author_active"])
        self.assertEqual(metadata["author_representation"], "typed_json_ast")
        self.assertEqual(compile_geometry_program(program).status, "compiled")
        self.assertEqual(metadata["authorship_admission"], admission.evidence())
        self.assertNotEqual(
            {node.provenance.get("source") for node in program.nodes},
            {CODEX_PROVIDER},
        )

    def test_importer_preserves_input_provenance_instead_of_relabelling_it(self):
        item = _valid_program_item()
        item["nodes"][0]["provenance"] = {
            "source": "untrusted_input_claim"
        }
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(directory, _manifest([item]))
            program = load_agent_authored_geometry_programs(
                path,
                admission=_admission(raw),
            )[0]
        self.assertEqual(
            program.node_map["seed"].provenance,
            {"source": "untrusted_input_claim"},
        )

    def test_importer_applies_paid_author_program_context_fail_closed(self):
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(
                directory,
                _manifest([_valid_program_item()]),
            )
            with self.assertRaises(AgentAuthoredSupplyError):
                load_agent_authored_geometry_programs(
                    path,
                    admission=_admission(raw),
                    author_context={
                        "program_context": {
                            "site_access_side_in_program_frame": "east",
                        },
                        "maximum_operator_depth": 2,
                        "downstream_body_rule_reserve": 1,
                    },
                )

    def test_persisted_geometry_program_dict_uses_the_same_typed_gate(self):
        with TemporaryDirectory() as directory:
            first_path, first_raw = _write_manifest(
                directory,
                _manifest([_valid_program_item()]),
            )
            persisted = load_agent_authored_geometry_programs(
                first_path,
                admission=_admission(first_raw),
            )[
                0
            ].to_dict()
            second_path = Path(directory) / "persisted-program.json"
            second_path.write_text(
                json.dumps(
                    {
                        **_manifest([persisted]),
                        "request_id": "task-4-request-002",
                    }
                ),
                encoding="utf-8",
            )
            second_raw = second_path.read_bytes()
            persisted_hash = GeometryProgram.from_dict(
                persisted
            ).program_hash()
            reloaded = load_agent_authored_geometry_programs(
                second_path,
                admission=_admission(
                    second_raw,
                    request_id="task-4-request-002",
                    program_hashes=(persisted_hash,),
                ),
            )

        self.assertEqual(len(reloaded), 1)
        self.assertEqual(reloaded[0].program_hash(), programs_hash := reloaded[0].metadata["author_program_hash"])
        self.assertEqual(programs_hash, GeometryProgram.from_dict(persisted).program_hash())

    def test_seed_supply_contains_only_validated_manifest_programs(self):
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(
                directory,
                _manifest([_valid_program_item()]),
            )
            admission = _admission(raw)
            programs = load_agent_authored_geometry_programs(
                path,
                admission=admission,
            )

        seeds = build_agent_authored_program_seeds(
            programs,
            building_type="근린생활시설",
            admission=admission,
        )
        self.assertEqual(len(seeds), 1)
        self.assertIn(
            "geometry_program_llm_author_active=True",
            seeds[0].notes,
        )
        payload = next(
            json.loads(note.split("=", 1)[1])
            for note in seeds[0].notes
            if note.startswith("geometry_program_payload=")
        )
        self.assertEqual(
            payload["metadata"]["author_provider"],
            CODEX_PROVIDER,
        )
        self.assertEqual(
            GeometryProgram.from_dict(payload).program_hash(),
            programs[0].program_hash(),
        )

    def test_seed_supply_does_not_round_robin_authored_geometry_across_legacy_hosts(self):
        from design.maas.grammar.verb_sequence import VerbSequence, call

        source_seeds = tuple(
            VerbSequence(
                name=f"carrier-{index}",
                label="carrier",
                calls=(call("base", proportion="site"),),
            )
            for index in range(4)
        )
        programs = tuple(
            SimpleNamespace(
                to_dict=lambda index=index: {"name": f"program-{index}"},
                program_hash=lambda index=index: f"{index + 1:064x}",
            )
            for index in range(5)
        )
        admission = SimpleNamespace(
            admitted_program_hashes=frozenset(
                program.program_hash() for program in programs
            )
        )

        with (
            patch(
                "design.maas.book_language.agent_authored_supply."
                "program_seed_sequences",
                return_value=source_seeds,
            ),
            patch(
                "design.maas.book_language.agent_authored_supply."
                "is_validated_codex_oauth_program_payload",
                return_value=True,
            ),
        ):
            seeds = build_agent_authored_program_seeds(
                programs,
                building_type="neighborhood",
                admission=admission,
            )

        self.assertEqual(len(seeds), 5)
        self.assertTrue(all(
            "geometry_program_source_seed=carrier-0" in seed.notes
            for seed in seeds
        ))
        self.assertFalse(any(
            "geometry_program_source_seed=carrier-1" in seed.notes
            for seed in seeds
        ))

    def test_seed_supply_preserves_manifest_ordinal_after_replay_filter(self):
        from design.maas.grammar.verb_sequence import VerbSequence, call

        source = VerbSequence(
            name="carrier-0",
            label="carrier",
            calls=(call("base", proportion="site"),),
        )
        programs = tuple(
            SimpleNamespace(
                metadata={"author_manifest_index": ordinal},
                to_dict=lambda ordinal=ordinal: {"name": f"program-{ordinal}"},
                program_hash=lambda ordinal=ordinal: f"{ordinal + 1:064x}",
            )
            for ordinal in (7, 12)
        )
        admission = SimpleNamespace(
            admitted_program_hashes=frozenset(
                program.program_hash() for program in programs
            )
        )

        with (
            patch(
                "design.maas.book_language.agent_authored_supply."
                "program_seed_sequences",
                return_value=(source,),
            ),
            patch(
                "design.maas.book_language.agent_authored_supply."
                "is_validated_codex_oauth_program_payload",
                return_value=True,
            ),
        ):
            seeds = build_agent_authored_program_seeds(
                programs,
                building_type="neighborhood",
                admission=admission,
            )

        self.assertIn("__codex_oauth_7_", seeds[0].name)
        self.assertIn("__codex_oauth_12_", seeds[1].name)

    def test_llm_candidate_requires_a_validated_paid_or_codex_identity(self):
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(
                directory,
                _manifest([_valid_program_item()]),
            )
            admission = _admission(raw)
            codex_program = load_agent_authored_geometry_programs(
                path,
                admission=admission,
            )[0]

        codex_candidate = _candidate(codex_program.to_dict())
        codex_candidate.source.metadata["geometry_program_bridge_evidence"] = {
            "llm_geometry_author_active": True,
            "author_provider": CODEX_PROVIDER,
            "initial_llm_authored_pre_book_program_hash": (
                codex_program.program_hash()
            ),
            "post_book_authored_program_hash": codex_program.program_hash(),
            "pre_book_lineage_parent_proof": {
                "program_hash": codex_program.program_hash(),
                "compiler_clean": True,
                "contained": True,
            },
        }
        self.assertFalse(_llm_authored_candidate(codex_candidate))
        self.assertTrue(_llm_authored_candidate(
            codex_candidate,
            codex_admission=admission,
        ))
        self.assertTrue(is_validated_codex_oauth_candidate(
            codex_candidate,
            admission=admission,
        ))

        forged_codex = replace(
            codex_program,
            metadata={
                **codex_program.metadata,
                "author_program_hash": "forged-program-hash",
            },
        )
        self.assertFalse(
            _llm_authored_candidate(
                _candidate(forged_codex.to_dict()),
                codex_admission=admission,
            )
        )

        paid_program = replace(
            codex_program,
            metadata={
                "author_provider": "openai_llm_geometry_author",
                "llm_geometry_author_active": True,
                "author_representation": "typed_json_ast",
                "author_response_id": "response-paid-001",
                "author_prompt_contract": (
                    "arr.maas.geometry_llm_author."
                    "v25_book_graph_principle_binding"
                ),
                "author_provider_request_kind": "geometry_author_initial",
            },
        )
        paid_candidate = _candidate(paid_program.to_dict())
        paid_candidate.source.metadata["geometry_program_bridge_evidence"] = {
            "llm_geometry_author_active": True,
            "author_provider": "openai_llm_geometry_author",
            "author_response_id": "response-paid-001",
            "initial_llm_authored_pre_book_program_hash": (
                paid_program.program_hash()
            ),
            "post_book_authored_program_hash": paid_program.program_hash(),
            "pre_book_lineage_parent_proof": {
                "program_hash": paid_program.program_hash(),
                "compiler_clean": True,
                "contained": True,
            },
        }
        # A caller-controlled provider label, response ID, and bridge are not
        # paid-provider admission.  The adapter's compiler-author boundary
        # must also have recorded its validated response diagnostics.
        self.assertFalse(_llm_authored_candidate(paid_candidate))
        for missing in (
            "llm_geometry_author_active",
            "author_representation",
            "author_response_id",
            "author_provider_request_kind",
        ):
            forged_payload = paid_program.to_dict()
            forged_payload["metadata"].pop(missing, None)
            self.assertFalse(
                _llm_authored_candidate(_candidate(forged_payload))
            )

        procedural = replace(
            codex_program,
            metadata={
                "author_provider": "bounded_procedural_geometry_agent",
                "llm_geometry_author_active": True,
                "author_representation": "typed_json_ast",
                "family": "llm_fake_label",
            },
        )
        self.assertFalse(
            _llm_authored_candidate(_candidate(procedural.to_dict()))
        )

    def test_post_book_codex_candidate_binds_admitted_parent_and_current_hash(self):
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(
                directory,
                _manifest([_valid_program_item()]),
            )
            admission = _admission(raw)
            pre_book_program = load_agent_authored_geometry_programs(
                path,
                admission=admission,
            )[0]

        seed = pre_book_program.node_map["seed"]
        post_book_program = replace(
            pre_book_program,
            nodes=tuple(
                replace(seed, parameters={**seed.parameters, "width": 1.1})
                if node.id == seed.id
                else node
                for node in pre_book_program.nodes
            ),
        )
        self.assertNotEqual(
            pre_book_program.program_hash(),
            post_book_program.program_hash(),
        )
        self.assertFalse(is_validated_codex_oauth_program_payload(
            post_book_program.to_dict(),
            admission=admission,
        ))
        candidate = _candidate(post_book_program.to_dict())
        candidate.source.metadata["geometry_program_bridge_evidence"] = {
            "llm_geometry_author_active": True,
            "author_provider": CODEX_PROVIDER,
            "initial_llm_authored_pre_book_program_hash": (
                pre_book_program.program_hash()
            ),
            "post_book_authored_program_hash": post_book_program.program_hash(),
            "pre_book_lineage_parent_proof": {
                "program_hash": pre_book_program.program_hash(),
                "compiler_clean": True,
                "contained": True,
            },
        }
        self.assertTrue(is_validated_codex_oauth_candidate(
            candidate,
            admission=admission,
        ))
        for field, forged_value in (
            ("initial_llm_authored_pre_book_program_hash", "f" * 64),
            ("post_book_authored_program_hash", "e" * 64),
        ):
            forged = _candidate(post_book_program.to_dict())
            forged.source.metadata["geometry_program_bridge_evidence"] = {
                **candidate.source.metadata["geometry_program_bridge_evidence"],
                field: forged_value,
            }
            self.assertFalse(is_validated_codex_oauth_candidate(
                forged,
                admission=admission,
            ))
        forged_proof = _candidate(post_book_program.to_dict())
        forged_proof.source.metadata["geometry_program_bridge_evidence"] = {
            **candidate.source.metadata["geometry_program_bridge_evidence"],
            "pre_book_lineage_parent_proof": {
                **candidate.source.metadata[
                    "geometry_program_bridge_evidence"
                ]["pre_book_lineage_parent_proof"],
                "program_hash": "d" * 64,
            },
        }
        self.assertFalse(is_validated_codex_oauth_candidate(
            forged_proof,
            admission=admission,
        ))

    def test_manifest_selection_pool_rejects_nontrusted_anchor(self):
        with TemporaryDirectory() as directory:
            path, raw = _write_manifest(
                directory,
                _manifest([_valid_program_item()]),
            )
            admission = _admission(raw)
            program = load_agent_authored_geometry_programs(
                path,
                admission=admission,
            )[0]
        trusted = _candidate(program.to_dict())
        trusted.source.metadata["geometry_program_bridge_evidence"] = {
            "llm_geometry_author_active": True,
            "author_provider": CODEX_PROVIDER,
            "initial_llm_authored_pre_book_program_hash": program.program_hash(),
            "post_book_authored_program_hash": program.program_hash(),
            "pre_book_lineage_parent_proof": {
                "program_hash": program.program_hash(),
                "compiler_clean": True,
                "contained": True,
            },
        }
        deterministic_anchor = _candidate(program.to_dict())
        deterministic_anchor.source.metadata[
            "authored_geometry_program"]["metadata"]["author_provider"] = (
                "bounded_procedural_geometry_agent"
            )
        retained, rejected_count = _trusted_codex_selection_pool(
            [trusted, deterministic_anchor],
            admission=admission,
        )
        self.assertEqual(retained, [trusted])
        self.assertEqual(rejected_count, 1)
