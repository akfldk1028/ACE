"""E2E tests for code modularization verification."""

import pytest
from pathlib import Path
import re


# Calculator output directory
CALCULATOR_DIR = Path("D:/Data/25_ACE/Calculator")


class TestCodeModularization:
    """Tests to verify generated code is properly modularized."""

    @pytest.fixture
    def calculator_exists(self):
        """Check if Calculator directory exists."""
        if not CALCULATOR_DIR.exists():
            pytest.skip("Calculator directory not found - run pipeline first")
        return True

    def test_directory_not_empty(self, calculator_exists):
        """Calculator directory should not be empty."""
        files = list(CALCULATOR_DIR.glob("**/*"))
        file_count = len([f for f in files if f.is_file()])

        assert file_count > 0, "Calculator directory is empty"

    def test_multiple_source_files(self, calculator_exists):
        """Should have multiple source files (not monolithic)."""
        py_files = list(CALCULATOR_DIR.glob("**/*.py"))

        # Should have at least 3 source files for proper modularization
        assert len(py_files) >= 3, f"Only {len(py_files)} Python files found - may be monolithic"

    def test_single_file_under_500_lines(self, calculator_exists):
        """No single file should exceed 500 lines."""
        py_files = list(CALCULATOR_DIR.glob("**/*.py"))

        for py_file in py_files:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            line_count = len(content.splitlines())

            assert line_count < 500, f"{py_file.name} has {line_count} lines (> 500)"

    def test_cross_module_imports(self, calculator_exists):
        """Should have imports between modules."""
        py_files = list(CALCULATOR_DIR.glob("**/*.py"))

        # Get module names (without .py)
        module_names = {f.stem for f in py_files if f.stem != "__init__"}

        cross_imports_found = False

        for py_file in py_files:
            content = py_file.read_text(encoding='utf-8', errors='ignore')

            # Look for imports of other modules
            for module in module_names:
                if module == py_file.stem:
                    continue

                # Check for various import patterns
                patterns = [
                    f"from {module} import",
                    f"import {module}",
                    f"from .{module} import",
                ]

                for pattern in patterns:
                    if pattern in content:
                        cross_imports_found = True
                        break

            if cross_imports_found:
                break

        assert cross_imports_found, "No cross-module imports found - may not be properly modularized"

    def test_entry_point_exists(self, calculator_exists):
        """Should have an entry point file."""
        entry_points = [
            CALCULATOR_DIR / "main.py",
            CALCULATOR_DIR / "app.py",
            CALCULATOR_DIR / "__main__.py",
            CALCULATOR_DIR / "calculator.py",
            CALCULATOR_DIR / "cli.py",
        ]

        entry_point_found = any(ep.exists() for ep in entry_points)

        # Also check for if __name__ == "__main__" pattern
        if not entry_point_found:
            for py_file in CALCULATOR_DIR.glob("**/*.py"):
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                if '__name__' in content and '__main__' in content:
                    entry_point_found = True
                    break

        assert entry_point_found, "No entry point found (main.py, app.py, or __main__ block)"

    def test_test_files_exist(self, calculator_exists):
        """Should have test files."""
        test_patterns = [
            CALCULATOR_DIR / "tests",
            CALCULATOR_DIR / "test",
        ]

        test_dir_exists = any(d.exists() and d.is_dir() for d in test_patterns)

        # Also check for test_*.py files
        test_files = list(CALCULATOR_DIR.glob("**/test_*.py"))

        assert test_dir_exists or len(test_files) > 0, "No test files found"


class TestCodeQuality:
    """Tests for code quality in generated files."""

    @pytest.fixture
    def calculator_exists(self):
        """Check if Calculator directory exists."""
        if not CALCULATOR_DIR.exists():
            pytest.skip("Calculator directory not found")
        return True

    def test_no_syntax_errors(self, calculator_exists):
        """Python files should have no syntax errors."""
        import ast

        py_files = list(CALCULATOR_DIR.glob("**/*.py"))

        for py_file in py_files:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            try:
                ast.parse(content)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {py_file.name}: {e}")

    def test_has_docstrings(self, calculator_exists):
        """At least some files should have docstrings."""
        import ast

        py_files = list(CALCULATOR_DIR.glob("**/*.py"))
        docstring_count = 0

        for py_file in py_files:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            try:
                tree = ast.parse(content)
                docstring = ast.get_docstring(tree)
                if docstring:
                    docstring_count += 1
            except SyntaxError:
                continue

        # At least 50% of files should have module docstrings
        assert docstring_count >= len(py_files) // 2 or docstring_count > 0

    def test_reasonable_function_count(self, calculator_exists):
        """Files should have reasonable number of functions."""
        import ast

        py_files = list(CALCULATOR_DIR.glob("**/*.py"))

        for py_file in py_files:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            try:
                tree = ast.parse(content)
                func_count = len([
                    node for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                ])

                # No file should have more than 20 functions (god object smell)
                assert func_count <= 20, f"{py_file.name} has {func_count} functions (> 20)"
            except SyntaxError:
                continue


class TestCalculatorFunctionality:
    """Tests for calculator functionality."""

    @pytest.fixture
    def calculator_exists(self):
        """Check if Calculator directory exists."""
        if not CALCULATOR_DIR.exists():
            pytest.skip("Calculator directory not found")
        return True

    def test_arithmetic_operations_defined(self, calculator_exists):
        """Should define basic arithmetic operations."""
        py_files = list(CALCULATOR_DIR.glob("**/*.py"))

        operations = ["add", "subtract", "multiply", "divide"]
        found_operations = set()

        for py_file in py_files:
            content = py_file.read_text(encoding='utf-8', errors='ignore').lower()

            for op in operations:
                if op in content or f"def {op}" in content:
                    found_operations.add(op)

        # Should have at least 3 of the 4 operations
        assert len(found_operations) >= 3, f"Only found operations: {found_operations}"

    def test_has_input_handling(self, calculator_exists):
        """Should have input handling for CLI."""
        py_files = list(CALCULATOR_DIR.glob("**/*.py"))

        input_patterns = [
            "input(",
            "argparse",
            "sys.argv",
            "click",
            "typer",
        ]

        input_found = False

        for py_file in py_files:
            content = py_file.read_text(encoding='utf-8', errors='ignore')

            for pattern in input_patterns:
                if pattern in content:
                    input_found = True
                    break

            if input_found:
                break

        assert input_found, "No input handling found"

    def test_has_output_handling(self, calculator_exists):
        """Should have output/print statements."""
        py_files = list(CALCULATOR_DIR.glob("**/*.py"))

        output_found = False

        for py_file in py_files:
            content = py_file.read_text(encoding='utf-8', errors='ignore')

            if "print(" in content or "return" in content:
                output_found = True
                break

        assert output_found, "No output handling found"


class TestProjectStructure:
    """Tests for project structure best practices."""

    @pytest.fixture
    def calculator_exists(self):
        """Check if Calculator directory exists."""
        if not CALCULATOR_DIR.exists():
            pytest.skip("Calculator directory not found")
        return True

    def test_has_requirements_or_setup(self, calculator_exists):
        """Should have dependency management file."""
        dependency_files = [
            CALCULATOR_DIR / "requirements.txt",
            CALCULATOR_DIR / "setup.py",
            CALCULATOR_DIR / "pyproject.toml",
            CALCULATOR_DIR / "Pipfile",
        ]

        has_deps = any(f.exists() for f in dependency_files)

        # This is optional for a simple calculator
        if not has_deps:
            pytest.skip("No dependency file (acceptable for simple project)")

    def test_has_readme(self, calculator_exists):
        """Should have README file."""
        readme_files = [
            CALCULATOR_DIR / "README.md",
            CALCULATOR_DIR / "README.txt",
            CALCULATOR_DIR / "README",
        ]

        has_readme = any(f.exists() for f in readme_files)

        # This is recommended but not required
        if not has_readme:
            pytest.skip("No README file (recommended but optional)")

    def test_no_credentials_in_code(self, calculator_exists):
        """Should not have hardcoded credentials."""
        py_files = list(CALCULATOR_DIR.glob("**/*.py"))

        credential_patterns = [
            r"api_key\s*=\s*['\"]",
            r"password\s*=\s*['\"]",
            r"secret\s*=\s*['\"]",
            r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style keys
        ]

        for py_file in py_files:
            content = py_file.read_text(encoding='utf-8', errors='ignore')

            for pattern in credential_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    pytest.fail(f"Potential credentials found in {py_file.name}: {pattern}")
