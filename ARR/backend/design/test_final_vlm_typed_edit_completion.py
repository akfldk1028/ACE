from types import SimpleNamespace
import unittest


from design.maas.book_language.typed_edit_completion import (
    complete_empty_final_vlm_geometry_edits,
)


class FinalVlmTypedEditCompletionTests(unittest.TestCase):
    def _audit(self):
        return {
            "source_sequence": "llm_puncture_notch",
            "hard_pass": False,
            "response_id": "resp-final-reject",
            "model": "test-model",
            "provider_critic_actions": [
                "too_box_like",
                "needs_carved_void",
            ],
            "locally_derived_critic_actions": ["wrong_program_typology"],
            "geometry_edits": [],
            "rationale": "The exact final solid needs a stronger carved identity.",
        }

    def _graph(self):
        return {
            "schema_version": "arr.maas.ai_readable_geometry_graph.v2",
            "root_id": "notch",
            "nodes": [
                {"id": "base", "operator": "box", "inputs": []},
                {"id": "notch", "operator": "subtract", "inputs": ["base"]},
            ],
            "edges": [{"source": "base", "target": "notch"}],
            "agent_edit_contract": {
                "protected_geometry_node_ids": ["base"],
                "operator_parameter_contracts": {
                    "box": ["width", "depth", "height"],
                    "subtract": [],
                    "bend": ["angle_degrees"],
                },
            },
        }

    def test_empty_normalized_edits_are_eligible_for_one_completion_turn(self):
        audit = self._audit()
        graph = self._graph()
        diversity = {
            "selected_families": ["split_wing", "bent_bar"],
            "underrepresented_families": ["punctured_court"],
        }
        requests = []

        def provider(request):
            requests.append(request)
            return {
                "response_id": "resp-completed-edits",
                "model": "test-model",
                "geometry_edits": [{
                    "operation": "set_parameter",
                    "target_node_id": "notch",
                    "parameter_name": "angle_degrees",
                    "numeric_value": 18.0,
                }],
                "rationale": "Use the graph contract to strengthen the existing notch.",
            }

        result = complete_empty_final_vlm_geometry_edits(
            audit,
            canonical_graph=graph,
            portfolio_diversity_context=diversity,
            provider=provider,
        )

        self.assertTrue(result["eligible"])
        self.assertTrue(result["requested"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["response_id"], "resp-completed-edits")
        self.assertEqual(result["edit_count"], 1)
        self.assertEqual(len(requests), 1)
        request = requests[0]
        self.assertEqual(request["exact_final_vlm_audit"]["response_id"], "resp-final-reject")
        self.assertEqual(request["canonical_geometry_graph"], graph)
        self.assertEqual(request["protected_geometry_node_ids"], ["base"])
        self.assertEqual(
            request["operator_parameter_contracts"],
            graph["agent_edit_contract"]["operator_parameter_contracts"],
        )
        self.assertEqual(request["portfolio_diversity_context"], diversity)
        self.assertEqual(request["required_geometry_edit_count"], {"minimum": 1, "maximum": 8})
        self.assertEqual(audit["geometry_edits"], result["geometry_edits"])
        self.assertEqual(audit["typed_edit_completion"], result)

    def test_completion_failure_is_persisted_and_cannot_consume_second_turn(self):
        audit = self._audit()
        calls = 0

        def provider(_request):
            nonlocal calls
            calls += 1
            return {
                "response_id": "resp-empty-again",
                "model": "test-model",
                "geometry_edits": [],
                "rationale": "No executable edit supplied.",
            }

        first = complete_empty_final_vlm_geometry_edits(
            audit,
            canonical_graph=self._graph(),
            portfolio_diversity_context={},
            provider=provider,
        )
        second = complete_empty_final_vlm_geometry_edits(
            audit,
            canonical_graph=self._graph(),
            portfolio_diversity_context={},
            provider=provider,
        )

        self.assertEqual(calls, 1)
        self.assertEqual(first, second)
        self.assertTrue(first["requested"])
        self.assertEqual(first["status"], "failed")
        self.assertEqual(first["failure_reasons"], ["completion_edit_count_out_of_bounds:0"])
        self.assertEqual(audit["geometry_edits"], [])


if __name__ == "__main__":
    unittest.main()
