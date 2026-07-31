import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.service_cache import load_verified_result, request_cache_key, store_verified_result


def _verified_result():
    feature = {
        "properties": {
            "source_signature": {"coherence_evidence": {"hard_pass": True}},
        }
    }
    return {
        "feature_collection": {"features": [feature for _ in range(20)]},
        "final_integer_projection": {"status": "optimal"},
        "final_vlm_completion": {"final_vlm_scored_count": 20},
    }


class MaasServiceCacheTest(SimpleTestCase):
    def test_verified_result_round_trip(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            "os.environ", {"MAAS_SERVICE_CACHE_DIR": directory}
        ):
            key = request_cache_key({"pnu": "1168011800104170004", "max_variants": 20})
            path = store_verified_result(key, _verified_result())
            self.assertEqual(path.parent, Path(directory))
            self.assertEqual(load_verified_result(key)["final_integer_projection"]["status"], "optimal")

    def test_refuses_fallback_result(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            "os.environ", {"MAAS_SERVICE_CACHE_DIR": directory}
        ):
            result = _verified_result()
            result["final_integer_projection"]["status"] = "infeasible_after_relaxation"
            with self.assertRaises(ValueError):
                store_verified_result("bad", result)
