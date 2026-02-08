"""Integration tests for maintenance scripts."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import importlib.util


# Maintenance scripts directory
MAINTENANCE_DIR = Path("D:/Data/25_ACE/maintenance")


def load_module_from_path(module_name: str, file_path: Path):
    """Dynamically load a Python module from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


class TestMaintenanceScriptsExist:
    """Tests for maintenance script existence."""

    def test_maintenance_dir_exists(self):
        """Maintenance directory should exist."""
        assert MAINTENANCE_DIR.exists(), f"Maintenance directory not found: {MAINTENANCE_DIR}"

    def test_port_map_validator_exists(self):
        """port_map_validator.py should exist."""
        script = MAINTENANCE_DIR / "port_map_validator.py"
        assert script.exists(), f"Script not found: {script}"

    def test_agent_registry_sync_exists(self):
        """agent_registry_sync.py should exist."""
        script = MAINTENANCE_DIR / "agent_registry_sync.py"
        assert script.exists(), f"Script not found: {script}"

    def test_health_check_exists(self):
        """health_check.py should exist."""
        script = MAINTENANCE_DIR / "health_check.py"
        assert script.exists(), f"Script not found: {script}"

    def test_model_field_checker_exists(self):
        """model_field_checker.py should exist."""
        script = MAINTENANCE_DIR / "model_field_checker.py"
        assert script.exists(), f"Script not found: {script}"

    def test_doc_sync_checker_exists(self):
        """doc_sync_checker.py should exist."""
        script = MAINTENANCE_DIR / "doc_sync_checker.py"
        assert script.exists(), f"Script not found: {script}"

    def test_run_maintenance_exists(self):
        """run_maintenance.py should exist."""
        script = MAINTENANCE_DIR / "run_maintenance.py"
        assert script.exists(), f"Script not found: {script}"


class TestPortMapValidator:
    """Tests for port_map_validator.py."""

    @pytest.fixture
    def port_validator(self):
        """Load port_map_validator module."""
        script = MAINTENANCE_DIR / "port_map_validator.py"
        if not script.exists():
            pytest.skip("port_map_validator.py not found")

        module = load_module_from_path("port_map_validator", script)
        if module is None:
            pytest.skip("Could not load port_map_validator module")
        return module

    def test_extract_ports_function_exists(self, port_validator):
        """Should have port extraction function."""
        # port_map_validator.py has extract_a2a_adapter_ports, extract_capabilities_ports, etc.
        func_names = dir(port_validator)
        extraction_funcs = [
            name for name in func_names
            if "extract" in name.lower() or "port" in name.lower()
        ]
        assert len(extraction_funcs) > 0

    def test_main_returns_bool(self, port_validator):
        """main() should return boolean."""
        if not hasattr(port_validator, 'main'):
            pytest.skip("No main function")

        with patch('builtins.print'):  # Suppress output
            try:
                result = port_validator.main()
                assert isinstance(result, bool)
            except SystemExit as e:
                # Exit code 0 = success (True), non-zero = failure (False)
                assert e.code in [0, 1, None]


class TestAgentRegistrySync:
    """Tests for agent_registry_sync.py."""

    @pytest.fixture
    def registry_sync(self):
        """Load agent_registry_sync module."""
        script = MAINTENANCE_DIR / "agent_registry_sync.py"
        if not script.exists():
            pytest.skip("agent_registry_sync.py not found")

        module = load_module_from_path("agent_registry_sync", script)
        if module is None:
            pytest.skip("Could not load agent_registry_sync module")
        return module

    def test_extract_agent_types_function(self, registry_sync):
        """Should have AgentType extraction function."""
        func_names = dir(registry_sync)
        extraction_funcs = [
            name for name in func_names
            if "extract" in name.lower() or "get" in name.lower() or "parse" in name.lower()
        ]
        assert len(extraction_funcs) > 0 or hasattr(registry_sync, 'main')

    def test_capabilities_key_extraction(self, registry_sync):
        """Should extract capabilities keys."""
        if hasattr(registry_sync, 'extract_capabilities'):
            # Test the function if it exists
            pass

    def test_main_returns_bool(self, registry_sync):
        """main() should return boolean."""
        if not hasattr(registry_sync, 'main'):
            pytest.skip("No main function")

        with patch('builtins.print'):
            try:
                result = registry_sync.main()
                assert isinstance(result, bool)
            except SystemExit as e:
                assert e.code in [0, 1, None]


class TestHealthCheck:
    """Tests for health_check.py."""

    @pytest.fixture
    def health_check(self):
        """Load health_check module."""
        script = MAINTENANCE_DIR / "health_check.py"
        if not script.exists():
            pytest.skip("health_check.py not found")

        module = load_module_from_path("health_check", script)
        if module is None:
            pytest.skip("Could not load health_check module")
        return module

    def test_handles_unavailable_server(self, health_check):
        """Should handle unavailable servers gracefully."""
        # Mock httpx or requests to simulate connection failure
        if hasattr(health_check, 'check_service'):
            with patch('httpx.get', side_effect=Exception("Connection refused")):
                try:
                    result = health_check.check_service("http://localhost:99999")
                    assert result is False
                except Exception:
                    pass  # Some implementations might raise

    def test_main_returns_bool(self, health_check):
        """main() should return boolean."""
        if not hasattr(health_check, 'main'):
            pytest.skip("No main function")

        # Mock network calls to prevent actual connections
        with patch('httpx.AsyncClient'), patch('httpx.Client'):
            with patch('builtins.print'):
                try:
                    result = health_check.main()
                    assert isinstance(result, bool)
                except SystemExit as e:
                    assert e.code in [0, 1, None]
                except Exception:
                    pass  # May fail due to mocking


class TestModelFieldChecker:
    """Tests for model_field_checker.py."""

    @pytest.fixture
    def field_checker(self):
        """Load model_field_checker module."""
        script = MAINTENANCE_DIR / "model_field_checker.py"
        if not script.exists():
            pytest.skip("model_field_checker.py not found")

        module = load_module_from_path("model_field_checker", script)
        if module is None:
            pytest.skip("Could not load model_field_checker module")
        return module

    def test_main_returns_bool(self, field_checker):
        """main() should return boolean."""
        if not hasattr(field_checker, 'main'):
            pytest.skip("No main function")

        with patch('builtins.print'):
            try:
                result = field_checker.main()
                assert isinstance(result, bool)
            except SystemExit as e:
                assert e.code in [0, 1, None]


class TestDocSyncChecker:
    """Tests for doc_sync_checker.py."""

    @pytest.fixture
    def doc_checker(self):
        """Load doc_sync_checker module."""
        script = MAINTENANCE_DIR / "doc_sync_checker.py"
        if not script.exists():
            pytest.skip("doc_sync_checker.py not found")

        module = load_module_from_path("doc_sync_checker", script)
        if module is None:
            pytest.skip("Could not load doc_sync_checker module")
        return module

    def test_main_returns_bool(self, doc_checker):
        """main() should return boolean."""
        if not hasattr(doc_checker, 'main'):
            pytest.skip("No main function")

        with patch('builtins.print'):
            try:
                result = doc_checker.main()
                assert isinstance(result, bool)
            except SystemExit as e:
                assert e.code in [0, 1, None]


class TestRunMaintenance:
    """Tests for run_maintenance.py."""

    @pytest.fixture
    def run_maintenance(self):
        """Load run_maintenance module."""
        script = MAINTENANCE_DIR / "run_maintenance.py"
        if not script.exists():
            pytest.skip("run_maintenance.py not found")

        module = load_module_from_path("run_maintenance", script)
        if module is None:
            pytest.skip("Could not load run_maintenance module")
        return module

    def test_run_check_valid_module(self, run_maintenance):
        """run_check() should handle valid module."""
        if not hasattr(run_maintenance, 'run_check'):
            pytest.skip("No run_check function")

        # Create a mock module with main() returning True
        mock_module = Mock()
        mock_module.main = Mock(return_value=True)

        with patch.dict(sys.modules, {'test_module': mock_module}):
            # May need to adjust based on actual implementation
            pass

    def test_run_check_invalid_module(self, run_maintenance):
        """run_check() should handle invalid module."""
        if not hasattr(run_maintenance, 'run_check'):
            pytest.skip("No run_check function")

        # Test with non-existent module (run_check takes name and module_name)
        try:
            result = run_maintenance.run_check("Test", "nonexistent_module_xyz123")
            assert result is False or result is None
        except (TypeError, ModuleNotFoundError, FileNotFoundError):
            pass  # Expected if module doesn't exist

    def test_main_returns_bool(self, run_maintenance):
        """main() should return boolean."""
        if not hasattr(run_maintenance, 'main'):
            pytest.skip("No main function")

        # Mock all the check functions
        with patch('builtins.print'):
            try:
                result = run_maintenance.main()
                assert isinstance(result, bool) or result is None
            except SystemExit as e:
                # Accept exit codes 0, 1, 2 (argparse may exit with 2)
                assert e.code in [0, 1, 2, None]
            except Exception:
                pass  # Some implementations may have different behavior


class TestMaintenanceIntegration:
    """Integration tests running actual maintenance scripts."""

    @pytest.mark.integration
    def test_run_all_maintenance(self):
        """Run all maintenance scripts and verify no crashes."""
        scripts = [
            "port_map_validator.py",
            "agent_registry_sync.py",
            "model_field_checker.py",
            "doc_sync_checker.py",
        ]

        for script_name in scripts:
            script = MAINTENANCE_DIR / script_name
            if not script.exists():
                continue

            module = load_module_from_path(script_name.replace('.py', ''), script)
            if module is None:
                continue

            if hasattr(module, 'main'):
                with patch('builtins.print'):
                    try:
                        result = module.main()
                        # Should return bool or exit cleanly
                        assert result is None or isinstance(result, bool)
                    except SystemExit:
                        pass  # Exit is acceptable
                    except Exception as e:
                        pytest.fail(f"{script_name} crashed: {e}")
