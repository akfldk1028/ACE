from __future__ import annotations

import importlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.geometry_language.outcome_graph import GeometryOutcomeGraph


def _design_memory_modules():
    try:
        config = importlib.import_module(
            "design.maas.design_memory.config"
        )
        adapter = importlib.import_module(
            "design.maas.design_memory.neo4j_adapter"
        )
    except ModuleNotFoundError as exc:
        raise AssertionError(
            "design-memory Neo4j isolation modules must exist"
        ) from exc
    return config, adapter


class RecordingNeo4jService:
    instances: list["RecordingNeo4jService"] = []

    def __init__(self, **kwargs):
        self.kwargs = dict(kwargs)
        self.queries: list[tuple[str, dict]] = []
        self.disconnected = False
        self.__class__.instances.append(self)

    def connect(self):
        return True

    def execute_write_query(self, query, parameters=None):
        self.queries.append((str(query), dict(parameters or {})))
        return []

    def disconnect(self):
        self.disconnected = True


class DesignMemorySettingsTests(SimpleTestCase):
    def test_absent_design_settings_disable_without_law_fallback(self):
        config, _adapter = _design_memory_modules()

        settings = config.DesignMemorySettings.from_environment({
            "NEO4J_URI": "bolt://law.internal:7687",
            "NEO4J_USER": "law-user",
            "NEO4J_PASSWORD": "law-secret",
            "NEO4J_DATABASE": "law",
        })

        self.assertFalse(settings.enabled)
        self.assertEqual(settings.reason, "not_enabled")
        self.assertEqual(settings.uri, "")
        self.assertEqual(settings.user, "")
        self.assertEqual(settings.password, "")
        self.assertEqual(settings.database, "")

    def test_incomplete_explicit_design_settings_fail_closed(self):
        config, _adapter = _design_memory_modules()

        settings = config.DesignMemorySettings.from_environment({
            "MAAS_DESIGN_MEMORY_NEO4J_ENABLED": "true",
            "MAAS_DESIGN_MEMORY_NEO4J_URI": "bolt://design:7687",
            "MAAS_DESIGN_MEMORY_NEO4J_DATABASE": "design",
        })

        self.assertFalse(settings.enabled)
        self.assertEqual(
            settings.reason,
            "incomplete_design_memory_settings",
        )
        self.assertEqual(
            set(settings.missing_fields),
            {"user", "password"},
        )

    def test_equal_law_uri_and_database_disable_mirroring(self):
        config, _adapter = _design_memory_modules()
        environment = {
            "MAAS_DESIGN_MEMORY_NEO4J_ENABLED": "on",
            "MAAS_DESIGN_MEMORY_NEO4J_URI": "bolt://shared:7687/",
            "MAAS_DESIGN_MEMORY_NEO4J_USER": "design-user",
            "MAAS_DESIGN_MEMORY_NEO4J_PASSWORD": "design-secret",
            "MAAS_DESIGN_MEMORY_NEO4J_DATABASE": "shared",
            "NEO4J_URI": "BOLT://SHARED:7687",
            "NEO4J_DATABASE": "shared",
        }

        settings = config.DesignMemorySettings.from_environment(environment)

        self.assertFalse(settings.enabled)
        self.assertEqual(settings.reason, "law_database_collision")

    def test_separate_design_database_preserves_explicit_credentials(self):
        config, _adapter = _design_memory_modules()
        environment = {
            "MAAS_DESIGN_MEMORY_NEO4J_ENABLED": "yes",
            "MAAS_DESIGN_MEMORY_NEO4J_URI": "bolt://graph:7687",
            "MAAS_DESIGN_MEMORY_NEO4J_USER": "design-user",
            "MAAS_DESIGN_MEMORY_NEO4J_PASSWORD": "design-secret",
            "MAAS_DESIGN_MEMORY_NEO4J_DATABASE": "maas-design",
            "NEO4J_URI": "bolt://graph:7687",
            "NEO4J_DATABASE": "law",
        }

        settings = config.DesignMemorySettings.from_environment(environment)

        self.assertTrue(settings.enabled)
        self.assertEqual(settings.reason, "enabled")
        self.assertEqual(settings.uri, "bolt://graph:7687")
        self.assertEqual(settings.user, "design-user")
        self.assertEqual(settings.password, "design-secret")
        self.assertEqual(settings.database, "maas-design")

    def test_settings_repr_does_not_expose_design_password(self):
        config, _adapter = _design_memory_modules()
        settings = config.DesignMemorySettings.from_environment({
            "MAAS_DESIGN_MEMORY_NEO4J_ENABLED": "yes",
            "MAAS_DESIGN_MEMORY_NEO4J_URI": "bolt://graph:7687",
            "MAAS_DESIGN_MEMORY_NEO4J_USER": "design-user",
            "MAAS_DESIGN_MEMORY_NEO4J_PASSWORD": "design-secret",
            "MAAS_DESIGN_MEMORY_NEO4J_DATABASE": "maas-design",
            "NEO4J_DATABASE": "law",
        })

        self.assertNotIn("design-secret", repr(settings))


class DesignMemoryNeo4jAdapterTests(SimpleTestCase):
    def setUp(self):
        RecordingNeo4jService.instances.clear()

    def _graph(self):
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")
        graph.nodes = {
            "node:a": {
                "id": "node:a",
                "kind": "geometry_program",
                "identity": "program-a",
                "attributes": {"program_hash": "a" * 64},
            },
            "node:b": {
                "id": "node:b",
                "kind": "outcome",
                "identity": "outcome-b",
                "attributes": {"hard_pass": True},
            },
        }
        graph.edges = {
            "edge:ab": {
                "id": "edge:ab",
                "source": "node:a",
                "target": "node:b",
                "kind": "yielded",
                "attributes": {"selected": True},
            },
        }
        return graph

    def _enabled_settings(self):
        config, _adapter = _design_memory_modules()
        return config.DesignMemorySettings.from_environment({
            "MAAS_DESIGN_MEMORY_NEO4J_ENABLED": "true",
            "MAAS_DESIGN_MEMORY_NEO4J_URI": "bolt://graph:7687",
            "MAAS_DESIGN_MEMORY_NEO4J_USER": "design-user",
            "MAAS_DESIGN_MEMORY_NEO4J_PASSWORD": "design-secret",
            "MAAS_DESIGN_MEMORY_NEO4J_DATABASE": "maas-design",
            "NEO4J_URI": "bolt://graph:7687",
            "NEO4J_DATABASE": "law",
        })

    def test_separate_database_is_passed_explicitly_to_service(self):
        _config, adapter_module = _design_memory_modules()
        adapter = adapter_module.DesignMemoryNeo4jAdapter(
            settings=self._enabled_settings(),
            service_factory=RecordingNeo4jService,
        )

        result = adapter.mirror(self._graph())

        self.assertEqual(result["status"], "mirrored")
        service = RecordingNeo4jService.instances[-1]
        self.assertEqual(service.kwargs, {
            "uri": "bolt://graph:7687",
            "user": "design-user",
            "password": "design-secret",
            "database": "maas-design",
        })
        self.assertTrue(service.disconnected)

    def test_payload_uses_only_design_labels_and_relationships(self):
        _config, adapter_module = _design_memory_modules()
        adapter = adapter_module.DesignMemoryNeo4jAdapter(
            settings=self._enabled_settings(),
            service_factory=RecordingNeo4jService,
        )

        result = adapter.mirror(self._graph())

        self.assertEqual(result["node_count"], 2)
        self.assertEqual(result["edge_count"], 1)
        service = RecordingNeo4jService.instances[-1]
        cypher = "\n".join(query for query, _params in service.queries)
        self.assertIn(":MaasDesignNode", cypher)
        self.assertIn(":MAAS_DESIGN_RELATION", cypher)
        self.assertNotIn("MaasGeometryOutcomeNode", cypher)
        self.assertNotIn("MAAS_GEOMETRY_RELATION", cypher)
        self.assertNotIn(":Law", cypher)
        self.assertNotIn(":Article", cypher)
        self.assertNotIn(":CONTAINS", cypher)
        node_parameters = service.queries[0][1]["nodes"]
        edge_parameters = service.queries[1][1]["edges"]
        self.assertEqual(len(node_parameters), 2)
        self.assertEqual(len(edge_parameters), 1)
        self.assertEqual(edge_parameters[0]["kind"], "yielded")

    def test_disabled_adapter_never_constructs_a_service(self):
        config, adapter_module = _design_memory_modules()
        adapter = adapter_module.DesignMemoryNeo4jAdapter(
            settings=config.DesignMemorySettings.from_environment({}),
            service_factory=RecordingNeo4jService,
        )

        result = adapter.mirror(self._graph())

        self.assertEqual(result["status"], "disabled")
        self.assertEqual(result["reason"], "not_enabled")
        self.assertEqual(RecordingNeo4jService.instances, [])

    def test_invalid_portable_graph_fails_without_constructing_service(self):
        _config, adapter_module = _design_memory_modules()
        adapter = adapter_module.DesignMemoryNeo4jAdapter(
            settings=self._enabled_settings(),
            service_factory=RecordingNeo4jService,
        )

        result = adapter.mirror(object())

        self.assertEqual(result["status"], "unavailable")
        self.assertIn("portable mapping", result["reason"])
        self.assertTrue(result["portable_graph_available"])
        self.assertEqual(RecordingNeo4jService.instances, [])

    def test_service_construction_failure_remains_optional(self):
        _config, adapter_module = _design_memory_modules()

        def fail_to_construct(**_kwargs):
            raise RuntimeError("factory unavailable")

        adapter = adapter_module.DesignMemoryNeo4jAdapter(
            settings=self._enabled_settings(),
            service_factory=fail_to_construct,
        )

        result = adapter.mirror(self._graph())

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "factory unavailable")
        self.assertTrue(result["portable_graph_available"])


class OutcomeGraphDesignMemoryBoundaryTests(SimpleTestCase):
    def test_legacy_outcome_flag_cannot_activate_a_database_write(self):
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")

        with patch.dict(
            os.environ,
            {"MAAS_OUTCOME_NEO4J": "1"},
            clear=True,
        ):
            result = graph.mirror_to_neo4j()

        self.assertEqual(result["status"], "disabled")
        self.assertEqual(result["reason"], "not_enabled")
        self.assertTrue(result["portable_graph_available"])

    def test_portable_save_remains_authority_when_mirror_is_disabled(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "outcome.json"
            graph = GeometryOutcomeGraph(path, pnu="test")
            graph.nodes = {
                "node:a": {
                    "id": "node:a",
                    "kind": "geometry_program",
                    "identity": "program-a",
                    "attributes": {},
                },
            }

            payload = graph.save()
            with patch.dict(os.environ, {}, clear=True):
                mirror = graph.mirror_to_neo4j()

            self.assertTrue(path.is_file())
            self.assertEqual(payload["node_count"], 1)
            self.assertEqual(mirror["status"], "disabled")
            self.assertTrue(mirror["portable_graph_available"])
