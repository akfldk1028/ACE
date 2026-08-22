from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from design.maas.agents.maas_geometry_agent.oauth_sharded_batch import (
    OauthShardError,
    merge_oauth_response_parts,
    merge_oauth_shards,
    plan_oauth_shards,
)


class MaasOauthShardedBatchTests(SimpleTestCase):
    def test_twenty_paths_are_partitioned_into_four_ordered_five_path_shards(self):
        path_ids = [f"book:path:{index:02d}" for index in range(20)]

        shards = plan_oauth_shards(path_ids, shard_size=5)

        self.assertEqual(len(shards), 4)
        self.assertEqual([len(shard.path_ids) for shard in shards], [5, 5, 5, 5])
        self.assertEqual(
            [path_id for shard in shards for path_id in shard.path_ids],
            path_ids,
        )

    def test_merge_preserves_exact_path_order_and_all_twenty_authored_items(self):
        path_ids = [f"book:path:{index:02d}" for index in range(20)]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            response_names = []
            for shard_index in range(4):
                name = f"response-{shard_index + 1}.json"
                response_names.append(name)
                start = shard_index * 5
                programs = [
                    {
                        "name": f"p{index:02d}",
                        "book_composition_path_id": path_ids[index],
                    }
                    for index in range(start, start + 5)
                ]
                (root / name).write_text(
                    json.dumps({"programs": programs}),
                    encoding="utf-8",
                )

            merged_path = merge_oauth_shards(
                root,
                response_names=response_names,
                expected_path_ids=path_ids,
                output_name="merged.json",
            )
            merged = json.loads(merged_path.read_text(encoding="utf-8"))

            self.assertEqual(len(merged["programs"]), 20)
            self.assertEqual(
                [item["book_composition_path_id"] for item in merged["programs"]],
                path_ids,
            )

    def test_merge_rejects_duplicate_path_identity(self):
        path_ids = [f"book:path:{index:02d}" for index in range(20)]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            programs = [
                {"name": f"p{index:02d}", "book_composition_path_id": path_ids[index]}
                for index in range(20)
            ]
            programs[-1]["book_composition_path_id"] = path_ids[0]
            names = []
            for shard_index in range(4):
                name = f"response-{shard_index + 1}.json"
                names.append(name)
                (root / name).write_text(
                    json.dumps({
                        "programs": programs[shard_index * 5:(shard_index + 1) * 5],
                    }),
                    encoding="utf-8",
                )

            with self.assertRaisesRegex(OauthShardError, "path identity mismatch"):
                merge_oauth_shards(
                    root,
                    response_names=names,
                    expected_path_ids=path_ids,
                    output_name="merged.json",
                )

    def test_micro_parts_merge_without_changing_authored_items(self):
        path_ids = [f"book:path:{index:02d}" for index in range(5)]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            names = []
            original_items = []
            for index, path_id in enumerate(path_ids):
                name = f"micro-{index}.json"
                item = {"name": f"p{index}", "book_composition_path_id": path_id}
                names.append(name)
                original_items.append(item)
                (root / name).write_text(
                    json.dumps({"programs": [item]}), encoding="utf-8"
                )

            output = merge_oauth_response_parts(
                root,
                response_names=names,
                expected_path_groups=[[path_id] for path_id in path_ids],
                output_name="micro-merged.json",
            )
            merged = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(merged["programs"], original_items)
