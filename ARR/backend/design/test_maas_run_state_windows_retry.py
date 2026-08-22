from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import os

from django.test import SimpleTestCase

from design.maas.geometry_language.run_state import write_run_state


class RunStateWindowsRetryTests(SimpleTestCase):
    def test_transient_windows_replace_lock_is_retried(self):
        original_replace = os.replace
        calls = 0

        def transient_replace(source, target):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise PermissionError(5, "sharing violation")
            return original_replace(source, target)

        with TemporaryDirectory() as temporary:
            with patch("os.replace", side_effect=transient_replace):
                output = write_run_state(
                    Path(temporary),
                    {"status": "running"},
                )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(calls, 2)
        self.assertEqual(payload, {"status": "running"})
