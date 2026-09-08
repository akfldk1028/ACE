"""Gate reuse must follow the executed operations and actual site context."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from shapely.geometry import box
from design.management.commands import generate_massv2 as runner


class VerdictCacheTests(TestCase):
    def test_nested_geometry_edit_invalidates_signature(self):
        original = Path.read_bytes
        def edited(path):
            content = original(path)
            return content + b'\n# changed operation\n' if path.name == 'grafting.py' else content
        before = runner._engine_signature()
        with patch.object(Path, 'read_bytes', edited):
            self.assertNotEqual(before, runner._engine_signature())

    def test_same_parcel_with_changed_actual_constraints_has_a_new_key(self):
        one = SimpleNamespace(pnu='same', context={'height': 12}, site_local_utm=box(0, 0, 20, 20))
        two = SimpleNamespace(pnu='same', context={'height': 9}, site_local_utm=box(0, 0, 20, 20))
        self.assertNotEqual(runner._site_signature(one, box(0, 0, 18, 18), (1, 0)),
                            runner._site_signature(two, box(0, 0, 18, 18), (1, 0)))
        self.assertNotEqual(runner._site_signature(one, box(0, 0, 18, 18), (1, 0)),
                            runner._site_signature(one, box(0, 0, 15, 18), (1, 0)))

    def test_unchanged_context_can_reuse_a_saved_verdict(self):
        with TemporaryDirectory() as tmp:
            with patch.object(runner, '_engine_signature', return_value='engine'):
                path = Path(tmp) / 'cache.json'
                cache = runner._VerdictCache(path, 'site')
                key = cache.key({'name': 'test'}, 3, 12)
                cache.put(key, {'outcome': 'mute'})
                cache.save()
                self.assertEqual(runner._VerdictCache(path, 'site').get(key), {'outcome': 'mute'})
