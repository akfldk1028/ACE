"""Append-only outcome graph for geometry-program mutation and selection.

The portable JSON graph is always available, including when Neo4j is off.
An optional Neo4j mirror can be enabled explicitly for interactive graph
inspection; failure to connect never blocks geometry diagnostics.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "arr.maas.geometry_mutation_outcome_graph.v1"


def _stable_id(kind: str, value: str) -> str:
    digest = hashlib.sha256(f"{kind}:{value}".encode("utf-8")).hexdigest()[:20]
    return f"{kind}:{digest}"


@dataclass
class GeometryOutcomeGraph:
    path: Path
    pnu: str
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: dict[str, dict[str, Any]] = field(default_factory=dict)
    observations: list[dict[str, Any]] = field(default_factory=list)
    _observation_index: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)
    _genotype_index: dict[tuple[str, str], list[dict[str, Any]]] = field(default_factory=dict, repr=False)
    _indexed_observation_count: int = field(default=-1, repr=False)

    @classmethod
    def load(cls, path: str | Path, *, pnu: str) -> "GeometryOutcomeGraph":
        graph = cls(Path(path), str(pnu))
        if not graph.path.exists():
            return graph
        try:
            payload = json.loads(graph.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return graph
        if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
            return graph
        if str(payload.get("pnu") or "") != str(pnu):
            return graph
        graph.nodes = {
            str(item["id"]): deepcopy(item)
            for item in payload.get("nodes") or ()
            if isinstance(item, dict) and item.get("id")
        }
        graph.edges = {
            str(item["id"]): deepcopy(item)
            for item in payload.get("edges") or ()
            if isinstance(item, dict) and item.get("id")
        }
        graph.observations = [
            deepcopy(item) for item in payload.get("observations") or ()
            if isinstance(item, dict)
        ]
        graph._ensure_observation_indices()
        return graph

    def observe_candidates(
        self,
        *,
        program_slug: str,
        candidates: Iterable[Any],
        downstream_report: dict[str, Any] | None,
        selected: Iterable[Any] = (),
    ) -> None:
        candidate_list = list(candidates)
        rows = list((downstream_report or {}).get("rows") or ())
        selected_keys = {_candidate_key(item) for item in selected}
        for index, candidate in enumerate(candidate_list):
            row = rows[index] if index < len(rows) and isinstance(rows[index], dict) else {}
            self._observe_candidate(
                program_slug=program_slug,
                candidate=candidate,
                downstream_row=row,
                selected=_candidate_key(candidate) in selected_keys,
            )

    def begin_program_run(self, program_slug: str) -> None:
        """Clear stale archive membership before a new causal observation run."""
        for item in self.observations:
            if item.get("program_slug") == str(program_slug):
                item["selected"] = False

    def observe_program_evaluation(
        self,
        *,
        program_slug: str,
        source: Any,
        sequence_name: str,
        principle_id: str,
        spatial: dict[str, Any],
        failed_gates: Iterable[str],
    ) -> None:
        """Persist pre-legal success *and failure* for the next mutation run.

        Earlier graph memory only contained candidates that had already passed
        the program gate.  Consequently the agent learned which legal-fit
        strength survived downstream, but repeatedly regenerated every bend or
        wing genotype that failed coverage/coherence.  This observation closes
        that causal gap without requiring Neo4j.
        """
        program = source.metadata.get("geometry_program") or {}
        bridge = source.metadata.get("geometry_program_bridge_evidence") or {}
        if not isinstance(program, dict) or not isinstance(bridge, dict) or not bridge.get("program_hash"):
            return
        metadata = program.get("metadata") if isinstance(program.get("metadata"), dict) else {}
        projected_program_hash = str(bridge.get("program_hash") or "")
        # Learning identity is the reusable agent-authored genotype. BOOK
        # principle/scope is a downstream mutation context and intentionally
        # has its own nodes; otherwise every principle becomes an unrelated
        # program and graph feedback can never inform the next run.
        program_hash = str(metadata.get("pre_book_program_hash") or projected_program_hash)
        geometry_hash = str(bridge.get("geometry_hash") or "")
        seed_family = str(bridge.get("source_seed") or str(sequence_name).split("__book_", 1)[0])
        strength = round(float(bridge.get("legal_fit_strength") or 0.0), 4)
        scope = source.metadata.get("program_book_projection_evidence") or {}
        scope = scope.get("scope") if isinstance(scope, dict) else {}
        scope_label = str((scope or {}).get("base_volume_label") or "1/1")
        failures = sorted({str(value) for value in failed_gates})
        observation_key = "|".join((
            "program_gate", str(program_slug), seed_family, program_hash,
            str(strength), str(principle_id), scope_label, geometry_hash,
        ))
        observation_id = _stable_id("observation", observation_key)
        observation = {
            "id": observation_id,
            "stage": "program_gate",
            "program_slug": str(program_slug),
            "source_seed": seed_family,
            "program_hash": program_hash,
            "projected_program_hash": projected_program_hash,
            "geometry_hash": geometry_hash,
            "geometry_family": str(metadata.get("family") or source.metadata.get("family") or "recursive_solid"),
            "legal_fit_strength": strength,
            "book_principle_id": str(principle_id),
            "book_scope": scope_label,
            "program_hard_pass": not failures,
            "failed_program_gates": failures,
            "program_metrics": {
                key: round(float(spatial.get(key) or 0.0), 4)
                for key in (
                    "role_coverage_score", "dominant_component_ratio",
                    "dominant_ratio_score", "site_coverage_ratio",
                    "site_coverage_score", "hierarchy_score",
                )
            },
            "selected": False,
            "vlm_critic_score": metadata.get("vlm_critic_score"),
            "vlm_revision_generation": metadata.get("vlm_revision_generation"),
            "vlm_geometry_critic_active": bool(metadata.get("vlm_geometry_critic_active")),
        }
        self._upsert_observation(observation)

        program_node = self._upsert_node("geometry_program", program_hash, {
            "family": observation["geometry_family"],
            "name": str(program.get("name") or ""),
            "base_seed": str(metadata.get("base_seed") or ""),
            "operator_path": list(metadata.get("operator_path") or bridge.get("operator_path") or ()),
            "intent_tags": list(metadata.get("intent_tags") or ()),
        })
        seed_node = self._upsert_node("program_seed", seed_family, {"program_slug": str(program_slug)})
        genotype_node = self._upsert_node(
            "geometry_genotype",
            f"{seed_family}|{program_hash}|{strength}",
            {"program_hash": program_hash, "source_seed": seed_family, "legal_fit_strength": strength},
        )
        outcome_node = self._upsert_node("outcome", observation_id, observation)
        book_node = self._upsert_node("book_principle", str(principle_id), {})
        scope_node = self._upsert_node("book_scope", scope_label, {})
        self._upsert_edge(seed_node, genotype_node, "mutates_with")
        self._upsert_edge(program_node, genotype_node, "parameterizes")
        self._upsert_edge(genotype_node, outcome_node, "yielded")
        self._upsert_edge(book_node, outcome_node, "applied_to")
        self._upsert_edge(scope_node, outcome_node, "scoped")

    def _observe_candidate(
        self,
        *,
        program_slug: str,
        candidate: Any,
        downstream_row: dict[str, Any],
        selected: bool,
    ) -> None:
        source = candidate.source
        program = source.metadata.get("geometry_program") or {}
        bridge = source.metadata.get("geometry_program_bridge_evidence") or {}
        if not isinstance(program, dict) or not isinstance(bridge, dict) or not bridge.get("program_hash"):
            return
        metadata = program.get("metadata") if isinstance(program.get("metadata"), dict) else {}
        projected_program_hash = str(bridge.get("program_hash") or "")
        program_hash = str(metadata.get("pre_book_program_hash") or projected_program_hash)
        geometry_hash = str(bridge.get("geometry_hash") or "")
        seed_family = str(bridge.get("source_seed") or _seed_family(candidate))
        strength = round(float(bridge.get("legal_fit_strength") or 0.0), 4)
        family = str(metadata.get("family") or source.metadata.get("family") or "recursive_solid")
        scope = source.metadata.get("program_book_projection_evidence") or {}
        scope = scope.get("scope") if isinstance(scope, dict) else {}
        scope_label = str((scope or {}).get("base_volume_label") or "1/1")
        legal = downstream_row.get("legal_projection") if isinstance(downstream_row.get("legal_projection"), dict) else {}
        parking = downstream_row.get("parking_hard_gate") if isinstance(downstream_row.get("parking_hard_gate"), dict) else {}
        observation_key = "|".join((
            str(program_slug), seed_family, program_hash, str(strength),
            str(candidate.principle_id), scope_label, geometry_hash,
        ))
        observation_id = _stable_id("observation", observation_key)
        observation = {
            "id": observation_id,
            "program_slug": str(program_slug),
            "source_seed": seed_family,
            "program_hash": program_hash,
            "projected_program_hash": projected_program_hash,
            "geometry_hash": geometry_hash,
            "geometry_family": family,
            "legal_fit_strength": strength,
            "book_principle_id": str(candidate.principle_id),
            "book_scope": scope_label,
            "program_hard_pass": True,
            "legal_hard_pass": bool(legal.get("hard_pass")),
            "geometry_retention_pass": bool(legal.get("geometry_retention_pass")),
            "volume_retention": round(float(legal.get("volume_retention") or 0.0), 4),
            "parking_hard_pass": bool(parking.get("hard_pass")),
            "combined_hard_pass": bool(downstream_row.get("combined_hard_pass")),
            "selected": bool(selected),
            "geometry_failure_reasons": sorted(str(value) for value in legal.get("geometry_failure_reasons") or ()),
            "vlm_critic_score": metadata.get("vlm_critic_score"),
            "vlm_revision_generation": metadata.get("vlm_revision_generation"),
            "vlm_geometry_critic_active": bool(metadata.get("vlm_geometry_critic_active")),
        }
        self._upsert_observation(observation)

        program_node = self._upsert_node("geometry_program", program_hash, {
            "family": family,
            "name": str(program.get("name") or ""),
            "base_seed": str(metadata.get("base_seed") or ""),
            "operator_path": list(metadata.get("operator_path") or bridge.get("operator_path") or ()),
            "intent_tags": list(metadata.get("intent_tags") or ()),
        })
        seed_node = self._upsert_node("program_seed", seed_family, {"program_slug": str(program_slug)})
        genotype_node = self._upsert_node(
            "geometry_genotype",
            f"{seed_family}|{program_hash}|{strength}",
            {"program_hash": program_hash, "source_seed": seed_family, "legal_fit_strength": strength},
        )
        outcome_node = self._upsert_node("outcome", observation_id, observation)
        book_node = self._upsert_node("book_principle", str(candidate.principle_id), {})
        scope_node = self._upsert_node("book_scope", scope_label, {})
        self._upsert_edge(seed_node, genotype_node, "mutates_with")
        self._upsert_edge(program_node, genotype_node, "parameterizes")
        self._upsert_edge(genotype_node, outcome_node, "yielded")
        self._upsert_edge(book_node, outcome_node, "applied_to")
        self._upsert_edge(scope_node, outcome_node, "scoped")

    def preferred_strengths(
        self,
        *,
        source_seed: str,
        program_hash: str,
        fallback: Iterable[float],
        limit: int = 3,
    ) -> tuple[float, ...]:
        buckets: dict[float, list[dict[str, Any]]] = defaultdict(list)
        for item in self._observations_for_genotype(source_seed, program_hash):
            buckets[round(float(item.get("legal_fit_strength") or 0.0), 4)].append(item)
        ranked = sorted(
            buckets,
            key=lambda strength: (
                sum(bool(item.get("program_hard_pass")) for item in buckets[strength]) / len(buckets[strength]),
                sum(bool(item.get("combined_hard_pass")) for item in buckets[strength]) / len(buckets[strength]),
                # Among hard-pass genotypes preserve the authored design mesh.
                # Upper-envelope interpolation is legal adaptation, not a
                # design reward; a lower strength therefore ranks first.
                -strength,
                sum(float(item.get("volume_retention") or 0.0) for item in buckets[strength]) / len(buckets[strength]),
            ),
            reverse=True,
        )
        successful = [
            strength for strength in ranked
            if any(item.get("combined_hard_pass") for item in buckets[strength])
        ]
        if successful:
            # Exploit the least-deforming successful fit only. Multiplying a
            # known-good genotype by stronger legal interpolation recreated
            # the same pyramidal family and consumed the topology budget.
            return (successful[0],)
        if ranked:
            exploration = [ranked[0]]
            exploration.extend(
                strength for strength in dict.fromkeys(
                    max(0.0, min(1.0, round(float(value), 4))) for value in fallback
                )
                if strength not in buckets
            )
            return tuple(exploration[: max(1, int(limit))])
        return tuple(dict.fromkeys(
            max(0.0, min(1.0, round(float(value), 4))) for value in fallback
        ))[: max(1, int(limit))]

    def preferred_book_principle_ids(
        self,
        *,
        source_seed: str,
        program_hash: str,
        fallback: Iterable[str],
        limit: int = 12,
    ) -> tuple[str, ...]:
        """Retrieve a scope-balanced successful BOOK neighborhood.

        The graph never authors geometry. It only reorders typed principles
        already present in the 59-principle registry using measured prior
        program/legal outcomes for the same reusable genotype.
        """
        maximum = max(6, int(limit))
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in self._observations_for_genotype(source_seed, program_hash):
            principle_id = str(item.get("book_principle_id") or "")
            if principle_id:
                buckets[principle_id].append(item)
        ranked = sorted(
            buckets,
            key=lambda principle_id: (
                sum(bool(item.get("combined_hard_pass")) for item in buckets[principle_id]) / len(buckets[principle_id]),
                sum(bool(item.get("program_hard_pass")) for item in buckets[principle_id]) / len(buckets[principle_id]),
                sum(float(item.get("volume_retention") or 0.0) for item in buckets[principle_id]) / len(buckets[principle_id]),
                len(buckets[principle_id]),
            ),
            reverse=True,
        )
        successful = [
            principle_id for principle_id in ranked
            if any(item.get("combined_hard_pass") for item in buckets[principle_id])
        ]
        usable = successful or [
            principle_id for principle_id in ranked
            if any(item.get("program_hard_pass") for item in buckets[principle_id])
        ]
        chosen: list[str] = []
        # One observed success per p.3 scope is selected first.
        for scope in ("1/1", "3/8", "1/2", "1/4", "1/8", "1/16"):
            match = next((
                principle_id for principle_id in usable
                if any(str(item.get("book_scope") or "") == scope for item in buckets[principle_id])
            ), "")
            if match and match not in chosen:
                chosen.append(match)
        # Preserve BOOK base/combination/aggregation sentence kinds when they
        # have succeeded for this exact genotype.
        for token in ("book:operative:", "book:combination:", "book:aggregation:"):
            match = next((item for item in usable if token in item and item not in chosen), "")
            if match:
                chosen.append(match)
        chosen.extend(item for item in usable if item not in chosen)
        chosen.extend(str(item) for item in fallback if str(item) not in chosen)
        return tuple(chosen[:maximum])

    def agent_neighborhood(
        self,
        *,
        source_seed: str,
        program_hash: str,
        limit: int = 8,
    ) -> dict[str, Any]:
        """Return compact measured memory that an LLM/VLM can safely consume."""
        rows = list(self._observations_for_genotype(source_seed, program_hash))
        ranked = sorted(
            rows,
            key=lambda item: (
                bool(item.get("combined_hard_pass")),
                bool(item.get("program_hard_pass")),
                bool(item.get("geometry_changed")),
                float(item.get("volume_retention") or 0.0),
            ),
            reverse=True,
        )[: max(1, int(limit))]
        failed_gates: Counter[str] = Counter()
        for item in rows:
            failed_gates.update(str(value) for value in item.get("failed_program_gates") or ())
            failed_gates.update(str(value) for value in item.get("geometry_failure_reasons") or ())
        return {
            "schema_version": "arr.maas.geometry_agent_neighborhood.v1",
            "source_seed": str(source_seed),
            "program_hash": str(program_hash),
            "observation_count": len(rows),
            "successful_strengths": sorted({
                float(item.get("legal_fit_strength") or 0.0)
                for item in rows if item.get("combined_hard_pass")
            }),
            "successful_book_principles": sorted({
                str(item.get("book_principle_id"))
                for item in rows if item.get("combined_hard_pass") and item.get("book_principle_id")
            })[:12],
            "common_failed_gates": [
                {"gate": gate, "count": count}
                for gate, count in failed_gates.most_common(8)
            ],
            "recent_measured_outcomes": [
                {
                    key: item.get(key)
                    for key in (
                        "stage", "program_hard_pass", "combined_hard_pass",
                        "legal_fit_strength", "book_principle_id", "book_scope",
                        "volume_retention", "critic_score", "critic_actions",
                        "geometry_changed", "mutation_status",
                    )
                    if item.get(key) is not None
                }
                for item in ranked
            ],
        }

    def observe_vlm_loop(
        self,
        *,
        program_slug: str,
        source_seed: str,
        trace: dict[str, Any],
    ) -> None:
        """Persist VLM reviews, typed edits, references, and revision proof."""
        for generation in trace.get("generations") or ():
            if not isinstance(generation, dict):
                continue
            for record in generation.get("records") or ():
                if not isinstance(record, dict) or record.get("status") != "critic_reviewed":
                    continue
                program_hash = str(record.get("program_hash") or "")
                geometry_hash = str(record.get("geometry_hash") or "")
                response_id = str(record.get("critic_response_id") or "")
                proof = record.get("revision_proof") if isinstance(record.get("revision_proof"), dict) else {}
                causal = record.get("vlm_causal_context") if isinstance(record.get("vlm_causal_context"), dict) else {}
                references = causal.get("reference_matches") if isinstance(causal.get("reference_matches"), list) else []
                memory = causal.get("outcome_memory") if isinstance(causal.get("outcome_memory"), dict) else {}
                observation_key = "|".join((
                    "vlm_critic", str(program_slug), str(source_seed), program_hash,
                    geometry_hash, response_id, str(record.get("generation") or 0),
                ))
                observation_id = _stable_id("observation", observation_key)
                observation = {
                    "id": observation_id,
                    "stage": "vlm_critic",
                    "program_slug": str(program_slug),
                    "source_seed": str(source_seed),
                    "program_hash": program_hash,
                    "geometry_hash": geometry_hash,
                    "critic_model": str(record.get("critic_model") or ""),
                    "critic_response_id": response_id,
                    "critic_score": float(record.get("critic_score") or 0.0),
                    "critic_actions": [str(item) for item in record.get("critic_actions") or ()],
                    "geometry_edits": deepcopy(record.get("geometry_edits") or []),
                    "mutation_status": str(record.get("mutation_status") or ""),
                    "geometry_changed": bool(proof.get("geometry_changed")),
                    "child_program_hash": str(proof.get("child_program_hash") or ""),
                    "child_geometry_hash": str(proof.get("child_geometry_hash") or ""),
                    "reference_ids": [
                        str(item.get("source_id") or item.get("title") or "")
                        for item in references if isinstance(item, dict)
                    ],
                    "memory_observation_count": int(memory.get("observation_count") or 0),
                }
                self._upsert_observation(observation)
                program_node = self._upsert_node("geometry_program", program_hash, {
                    "name": str(record.get("program") or ""),
                })
                critic_identity = response_id or observation_id
                critic_node = self._upsert_node("vlm_critic", critic_identity, {
                    "model": observation["critic_model"],
                    "score": observation["critic_score"],
                    "actions": observation["critic_actions"],
                })
                outcome_node = self._upsert_node("outcome", observation_id, observation)
                self._upsert_edge(program_node, critic_node, "reviewed_by")
                self._upsert_edge(critic_node, outcome_node, "proposed_typed_edit")
                if observation["child_program_hash"]:
                    child_node = self._upsert_node("geometry_program", observation["child_program_hash"], {
                        "geometry_hash": observation["child_geometry_hash"],
                    })
                    self._upsert_edge(program_node, child_node, "vlm_revised_to")
                for item in references:
                    if not isinstance(item, dict):
                        continue
                    identity = str(item.get("source_id") or item.get("title") or "")
                    if not identity:
                        continue
                    reference_node = self._upsert_node("reference", identity, {
                        "source": str(item.get("source") or ""),
                        "title": str(item.get("title") or ""),
                        "selection_role": str(item.get("selection_role") or ""),
                        "matched_tags": list(item.get("matched_tags") or ()),
                    })
                    self._upsert_edge(reference_node, critic_node, "informed")

    def save(self) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "pnu": self.pnu,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "observation_count": len(self.observations),
            "nodes": sorted(self.nodes.values(), key=lambda item: item["id"]),
            "edges": sorted(self.edges.values(), key=lambda item: item["id"]),
            "observations": sorted(self.observations, key=lambda item: item["id"]),
            "interactive_contract": {
                "node_identity": "stable id",
                "editable_node_kinds": ["geometry_program", "geometry_genotype"],
                "outcome_is_observation_only": True,
                "agent_query": "retrieve successful genotype neighborhood before proposing bounded mutations",
            },
        }

    def mirror_to_neo4j(self) -> dict[str, Any]:
        if os.getenv("MAAS_OUTCOME_NEO4J", "").strip().lower() not in {"1", "true", "yes", "on"}:
            return {"status": "disabled", "portable_graph_available": True}
        try:
            from graph_db.services.neo4j_service import Neo4jService
            service = Neo4jService()
            if not service.connect():
                return {"status": "unavailable", "reason": "connect_returned_false", "portable_graph_available": True}
            try:
                for node in self.nodes.values():
                    service.execute_query(
                        "MERGE (n:MaasGeometryOutcomeNode {id: $id}) SET n.kind=$kind, n.payload_json=$payload",
                        parameters={
                            "id": node["id"],
                            "kind": node["kind"],
                            "payload": json.dumps(node.get("attributes") or {}, ensure_ascii=False, sort_keys=True),
                        },
                    )
                for edge in self.edges.values():
                    service.execute_query(
                        "MATCH (a:MaasGeometryOutcomeNode {id:$source}), (b:MaasGeometryOutcomeNode {id:$target}) "
                        "MERGE (a)-[r:MAAS_GEOMETRY_RELATION {id:$id}]->(b) SET r.kind=$kind",
                        parameters=edge,
                    )
            finally:
                service.disconnect()
            return {"status": "mirrored", "node_count": len(self.nodes), "edge_count": len(self.edges)}
        except Exception as exc:  # graph DB is an optional mirror, never a geometry dependency
            return {"status": "unavailable", "reason": str(exc), "portable_graph_available": True}

    def _upsert_node(self, kind: str, identity: str, attributes: dict[str, Any]) -> str:
        node_id = _stable_id(kind, identity)
        record = self.nodes.setdefault(node_id, {"id": node_id, "kind": kind, "identity": identity, "attributes": {}})
        record["attributes"].update(deepcopy(attributes))
        return node_id

    def _ensure_observation_indices(self) -> None:
        if self._indexed_observation_count == len(self.observations):
            return
        self._observation_index = {
            str(item.get("id") or ""): item
            for item in self.observations
            if item.get("id")
        }
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for item in self.observations:
            grouped[(str(item.get("source_seed") or ""), str(item.get("program_hash") or ""))].append(item)
        self._genotype_index = dict(grouped)
        self._indexed_observation_count = len(self.observations)

    def _upsert_observation(self, observation: dict[str, Any]) -> None:
        self._ensure_observation_indices()
        observation_id = str(observation["id"])
        existing = self._observation_index.get(observation_id)
        if existing is not None:
            existing.update(observation)
            return
        self.observations.append(observation)
        self._observation_index[observation_id] = observation
        key = (str(observation.get("source_seed") or ""), str(observation.get("program_hash") or ""))
        self._genotype_index.setdefault(key, []).append(observation)
        self._indexed_observation_count = len(self.observations)

    def _observations_for_genotype(self, source_seed: str, program_hash: str) -> list[dict[str, Any]]:
        self._ensure_observation_indices()
        return self._genotype_index.get((str(source_seed), str(program_hash)), [])

    def _upsert_edge(self, source: str, target: str, kind: str) -> str:
        edge_id = _stable_id("edge", f"{source}|{kind}|{target}")
        self.edges[edge_id] = {"id": edge_id, "source": source, "target": target, "kind": kind}
        return edge_id


def _seed_family(candidate: Any) -> str:
    return str(candidate.sequence.name).split("__book_", 1)[0].split("__search_", 1)[0]


def _candidate_key(candidate: Any) -> tuple[str, str, str]:
    bridge = candidate.source.metadata.get("geometry_program_bridge_evidence") or {}
    return (
        str(candidate.sequence.name),
        str(candidate.principle_id),
        str(bridge.get("geometry_hash") or ""),
    )


__all__ = ["GeometryOutcomeGraph", "SCHEMA_VERSION"]
