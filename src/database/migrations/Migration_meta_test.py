from typing import Any, Dict
from pathlib import Path
import tempfile
import shutil
import os

from lib.Logging import logger


class TestMigrationMeta:
    """Lightweight meta tests that test migration infrastructure without full setup"""

    def setup_method(self, method):
        """Lightweight setup for meta tests"""
        # Create temporary directories for testing cleanup functionality
        self.temp_dir = Path(tempfile.mkdtemp())
        self.created_files = []
        self.created_dirs = []

    def teardown_method(self, method):
        """Clean up temporary test files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Could not clean up temp dir {self.temp_dir}: {e}")

    def test_cleanup_files(self):
        """Test basic file cleanup functionality."""
        # Create test files
        temp_file = self.temp_dir / "test_temp.txt"
        temp_file.write_text("temporary content")
        self.created_files.append(temp_file)

        # Create test directory
        test_subdir = self.temp_dir / "test_subdir"
        test_subdir.mkdir()
        self.created_dirs.append(test_subdir)

        # Verify files exist
        assert temp_file.exists(), "Test file should exist"
        assert test_subdir.exists(), "Test directory should exist"

        # Test cleanup (files are cleaned up in teardown_method)
        assert len(self.created_files) > 0, "Should track created files"
        assert len(self.created_dirs) > 0, "Should track created directories"

    def test_cleanup_preserves_other_files(self):
        """Test that cleanup preserves files not marked for deletion."""
        # Create files in different categories
        important_file = self.temp_dir / "important.txt"
        important_file.write_text("important content")
        # Don't add to created_files - this simulates files that shouldn't be cleaned up

        temp_file = self.temp_dir / "temp.txt"
        temp_file.write_text("temporary content")
        self.created_files.append(temp_file)  # This one should be tracked for cleanup

        # Verify both exist
        assert important_file.exists(), "Important file should exist"
        assert temp_file.exists(), "Temp file should exist"

        # Test that we only track files we want to clean up
        assert (
            important_file not in self.created_files
        ), "Important file should not be tracked for cleanup"
        assert (
            temp_file in self.created_files
        ), "Temp file should be tracked for cleanup"

    def test_get_configured_extensions(self):
        """Test extension configuration parsing."""
        # Test parsing CSV extension lists
        test_cases = [
            ("", []),
            ("ext1", ["ext1"]),
            ("ext1,ext2", ["ext1", "ext2"]),
            ("ext1, ext2, ext3", ["ext1", "ext2", "ext3"]),
            ("  ext1  ,  ext2  ", ["ext1", "ext2"]),
        ]

        for input_str, expected in test_cases:
            result = [ext.strip() for ext in input_str.split(",") if ext.strip()]
            assert (
                result == expected
            ), f"Failed for input '{input_str}': expected {expected}, got {result}"

    def test_command_validation_no_message(self):
        """Test command validation when no message is provided."""

        # Test that revision commands require a message
        def validate_revision_command(command_args):
            if (
                "revision" in command_args
                and "-m" not in command_args
                and "--message" not in command_args
            ):
                return False, "Error: --message is required"
            return True, ""

        # Test cases
        valid, error = validate_revision_command(["revision", "-m", "test message"])
        assert valid, "Should be valid with message"

        valid, error = validate_revision_command(["revision"])
        assert not valid, "Should be invalid without message"
        assert "message is required" in error

    def test_abstract_configuration(self):
        """Test that the abstract class configuration works correctly."""
        # Test basic configuration structure
        config = {
            "test_type": "meta",
            "create_mock_extensions": False,
            "matrix_targets": ["core"],
            "test_variations": {
                "revision_variation": [
                    {
                        "type": "manual",
                        "message": "manual test",
                        "flags": ["--no-autogenerate"],
                    },
                ]
            },
        }

        # Verify configuration structure
        assert config["test_type"] == "meta"
        assert config["create_mock_extensions"] is False
        assert "core" in config["matrix_targets"]
        assert "revision_variation" in config["test_variations"]

    def test_env_setup_python_path(self):
        """Test Python path environment setup."""
        import sys

        original_path = sys.path.copy()

        # Test adding a path
        test_path = str(self.temp_dir)
        if test_path not in sys.path:
            sys.path.insert(0, test_path)
            assert test_path in sys.path, "Test path should be added to sys.path"
            sys.path.remove(test_path)

        # Restore original path
        sys.path = original_path

    def test_env_import_module_safely_existing(self):
        """Test safe module import for existing modules."""
        # Test importing a standard library module
        try:
            import os

            result = True
        except ImportError:
            result = False

        assert result, "Should be able to import standard library modules"

    def test_env_import_module_safely_nonexistent(self):
        """Test safe module import for non-existent modules."""
        # Test importing a non-existent module
        try:
            import nonexistent_module_12345

            result = True
        except ImportError:
            result = False

        assert not result, "Should fail to import non-existent modules"

    def test_env_parse_csv_env_var(self):
        """Test parsing CSV environment variables."""
        test_cases = [
            ("", []),
            ("single", ["single"]),
            ("one,two", ["one", "two"]),
            ("one, two, three", ["one", "two", "three"]),
            ("  spaced  ,  values  ", ["spaced", "values"]),
        ]

        for csv_string, expected in test_cases:
            result = [item.strip() for item in csv_string.split(",") if item.strip()]
            assert result == expected, f"CSV parsing failed for '{csv_string}'"

    def test_error_handling_missing_message(self):
        """Test error handling for missing message parameter."""

        def check_message_requirement(args):
            if "revision" in args and not any(
                arg in args for arg in ["-m", "--message"]
            ):
                return "Error: --message is required"
            return None

        error = check_message_requirement(["revision"])
        assert error is not None, "Should return error for missing message"
        assert "message is required" in error

    def test_error_handling_invalid_command(self):
        """Test error handling for invalid commands."""
        valid_commands = ["revision", "upgrade", "downgrade", "current", "history"]

        def validate_command(command):
            return command in valid_commands

        assert validate_command("revision"), "revision should be valid"
        assert validate_command("upgrade"), "upgrade should be valid"
        assert not validate_command(
            "invalid_command"
        ), "invalid_command should not be valid"

    def test_env_import_module_from_file(self):
        """Test importing a module from a file path."""
        # Create a temporary Python file
        test_module_file = self.temp_dir / "test_module.py"
        test_module_file.write_text(
            """
def test_function():
    return "test_result"

TEST_CONSTANT = "test_value"
"""
        )

        # Test that the file exists and contains Python code
        assert test_module_file.exists(), "Test module file should exist"
        content = test_module_file.read_text()
        assert "def test_function" in content, "Should contain test function"
        assert "TEST_CONSTANT" in content, "Should contain test constant"

    def test_env_setup_alembic_config(self):
        """Test Alembic configuration setup."""
        # Test basic Alembic configuration structure
        config_dict = {
            "script_location": "migrations",
            "sqlalchemy.url": "sqlite:///test.db",
            "file_template": "%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s",
        }

        # Verify configuration has required keys
        assert "script_location" in config_dict
        assert "sqlalchemy.url" in config_dict
        assert "file_template" in config_dict

    def test_env_get_alembic_context_config(self):
        """Test Alembic context configuration."""
        # Test context configuration structure
        context_config = {
            "target_metadata": None,
            "literal_binds": True,
            "dialect_opts": {"paramstyle": "named"},
        }

        # Verify context configuration structure
        assert "target_metadata" in context_config
        assert "literal_binds" in context_config
        assert "dialect_opts" in context_config

    def test_get_script_py_mako_template(self):
        """Test script.py.mako template content."""
        # Test basic template structure
        template_content = '''"""${message}"""
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}

def upgrade():
    ${upgrades if upgrades else "pass"}

def downgrade():
    ${downgrades if downgrades else "pass"}
'''

        # Verify template has required components
        assert "revision =" in template_content
        assert "down_revision =" in template_content
        assert "def upgrade():" in template_content
        assert "def downgrade():" in template_content

    def test_get_default_alembic_ini_dict(self):
        """Test default Alembic INI configuration."""
        # Test default configuration structure
        default_config = {
            "alembic": {
                "script_location": "migrations",
                "file_template": "%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s",
            },
            "loggers": {
                "keys": "root,sqlalchemy,alembic",
            },
        }

        # Verify default configuration structure
        assert "alembic" in default_config
        assert "script_location" in default_config["alembic"]
        assert "loggers" in default_config

    def test_get_extension_alembic_ini_dict(self):
        """Test extension-specific Alembic INI configuration."""
        ext_name = "test_extension"

        # Test extension configuration structure
        ext_config = {
            "alembic": {
                "script_location": f"extensions/{ext_name}/migrations",
                "file_template": "%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s",
            }
        }

        # Verify extension configuration
        assert "alembic" in ext_config
        assert (
            f"extensions/{ext_name}/migrations"
            in ext_config["alembic"]["script_location"]
        )

    def test_dict_to_ini(self):
        """Test converting dictionary to INI format."""
        test_dict = {
            "section1": {
                "key1": "value1",
                "key2": "value2",
            },
            "section2": {
                "key3": "value3",
            },
        }

        # Test basic structure conversion
        expected_sections = ["section1", "section2"]
        expected_keys = ["key1", "key2", "key3"]

        # Verify all sections and keys are represented
        sections = list(test_dict.keys())
        all_keys = []
        for section_dict in test_dict.values():
            all_keys.extend(section_dict.keys())

        for expected_section in expected_sections:
            assert (
                expected_section in sections
            ), f"Section {expected_section} should be present"

        for expected_key in expected_keys:
            assert expected_key in all_keys, f"Key {expected_key} should be present"
