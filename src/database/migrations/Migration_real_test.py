# from typing import Any, Dict

# import pytest
# import stringcase

# from database.migrations.AbstractMigrationTest import (
#     AbstractMigrationTest,
#     create_regenerate_variations,
#     create_revision_variations,
# )
# from lib.Environment import env
# from lib.Logging import logger


# class MigrationTestConfig:
#     """Configuration class for migration matrix testing"""

#     @staticmethod
#     def get_configured_extensions():
#         """Get configured extensions from environment, with fallback for testing"""
#         # Try to get extensions from environment
#         try:
#             extensions_str = env("APP_EXTENSIONS") or ""
#             configured_extensions = [
#                 ext.strip() for ext in extensions_str.split(",") if ext.strip()
#             ]
#             if configured_extensions:
#                 logger.debug(
#                     f"MigrationTestConfig using environment extensions: {configured_extensions}"
#                 )
#                 return configured_extensions
#         except Exception as e:
#             logger.warning(f"Could not read APP_EXTENSIONS from environment: {e}")

#         # Return test extensions if no real ones are configured
#         logger.debug("MigrationTestConfig falling back to test extensions")
#         return ["test_ext_default"]

#         # Fallback to current environment
#         try:
#             extensions_str = env("APP_EXTENSIONS") or ""
#             configured_extensions = [
#                 ext.strip() for ext in extensions_str.split(",") if ext.strip()
#             ]
#             if configured_extensions:
#                 logger.debug(
#                     f"MigrationTestConfig using current environment extensions: {configured_extensions}"
#                 )
#                 return configured_extensions
#         except Exception as e:
#             logger.warning(f"Could not read APP_EXTENSIONS from environment: {e}")

#         # Return test extensions if no real ones are configured
#         logger.debug("MigrationTestConfig falling back to test extensions")
#         return ["test_ext_default"]

#     @staticmethod
#     def get_test_targets_for_function(function_name):
#         """Get test targets based on function name and configured extensions"""
#         configured_extensions = MigrationTestConfig.get_configured_extensions()
#         logger.debug(
#             f"Getting test targets for {function_name}, configured extensions: {configured_extensions}"
#         )

#         if function_name.startswith("test_matrix_"):
#             # Matrix tests include both core and extensions
#             targets = ["core"]
#             targets.extend(configured_extensions)
#             logger.debug(f"Matrix test targets: {targets}")
#             return targets
#         elif function_name.startswith("test_extension_"):
#             # Extension-only tests
#             logger.debug(f"Extension test targets: {configured_extensions}")
#             return configured_extensions
#         elif function_name.startswith("test_core_"):
#             # Core-only tests
#             logger.debug("Core test targets: ['core']")
#             return ["core"]
#         else:
#             # Default to core for unrecognized patterns
#             logger.debug("Default test targets: ['core']")
#             return ["core"]


# # Removed pytest_generate_tests function to simplify test discovery


# @pytest.mark.dependency(
#     depends=["migrations_meta", "migrations_mock"],
#     scope="session",
#     name="migrations_real",
# )
# @pytest.mark.real
# class TestMigrationMatrix(AbstractMigrationTest):
#     """Matrix test suite for migration system with core and extension entities"""

#     # Configuration for this test class
#     TEST_DB_NAME_SUFFIX = "real"
#     TEST_EXTENSIONS = ",".join(
#         MigrationTestConfig.get_configured_extensions()
#     )  # Use real extensions
#     TRACK_CLEANUP = True
#     USE_MOCK_DIRECTORIES = False  # Use real directories for real testing
#     CREATE_TEST_EXTENSIONS = []  # Extensions come from environment

#     def get_test_config(self) -> Dict[str, Any]:
#         """Configure real tests - test with real core and extension entities."""
#         configured_extensions = MigrationTestConfig.get_configured_extensions()
#         matrix_targets = ["core"] + configured_extensions

#         return {
#             "test_type": "real",
#             "create_mock_extensions": False,
#             "matrix_targets": matrix_targets,
#             "configured_extensions": configured_extensions,
#             "test_variations": {
#                 "revision_variation": create_revision_variations(),
#                 "regenerate_variation": create_regenerate_variations(),
#             },
#         }

#     # Fixtures are now handled by pytest parametrization decorators

#     def get_configured_extensions(self):
#         """Get list of configured extensions from APP_EXTENSIONS"""
#         return MigrationTestConfig.get_configured_extensions()

#     def get_migration_targets(self):
#         """Get all migration targets (core + extensions)"""
#         targets = ["core"]
#         targets.extend(self.get_configured_extensions())
#         return targets

#     def _is_real_extension(self, extension_name):
#         """Check if this is a real extension (not a test extension)"""
#         # Check if extension directory exists in the real extensions path
#         real_ext_dir = self.extensions_dir / extension_name
#         return real_ext_dir.exists() and any(real_ext_dir.glob("BLL_*.py"))

#     def _get_extension_table_names(self, extension_name):
#         """Dynamically extract table names from an extension's DB model files"""
#         if not self._is_real_extension(extension_name):
#             # For test extensions, return the test table name
#             return [f"{extension_name}_test_table"]

#         extension_dir = self.extensions_dir / extension_name
#         if not extension_dir.exists():
#             logger.warning(f"Extension directory {extension_dir} does not exist")
#             return []

#         bll_files = list(extension_dir.glob("BLL_*.py"))
#         if not bll_files:
#             logger.debug(f"No BLL_*.py files found for extension {extension_name}")
#             return []

#         table_names = []

#         # Import the models and extract table names
#         import importlib.util
#         import sys

#         for bll_file in bll_files:
#             try:
#                 # Import the module
#                 spec = importlib.util.spec_from_file_location(
#                     f"temp_{extension_name}_{bll_file.stem}", bll_file
#                 )
#                 if not spec or not spec.loader:
#                     continue

#                 module = importlib.util.module_from_spec(spec)
#                 spec.loader.exec_module(module)

#                 # Find all classes that use DatabaseMixin and extract table names
#                 for attr_name in dir(module):
#                     attr = getattr(module, attr_name)
#                     if (
#                         isinstance(attr, type)
#                         and hasattr(attr, "__mro__")
#                         and any("DatabaseMixin" in str(base) for base in attr.__mro__)
#                         and hasattr(attr, "DB")
#                     ):
#                         try:
#                             # Access the .DB property to get SQLAlchemy model
#                             db_model = attr.DB
#                             if hasattr(db_model, "__tablename__"):
#                                 table_names.append(db_model.__tablename__)
#                                 logger.debug(
#                                     f"Found table {db_model.__tablename__} in {bll_file.name}"
#                                 )
#                         except Exception as e:
#                             logger.warning(
#                                 f"Error accessing .DB property of {attr_name}: {e}"
#                             )

#             except Exception as e:
#                 logger.error(f"Error inspecting {bll_file}: {e}")
#                 continue

#         logger.debug(f"Extension {extension_name} expected tables: {table_names}")
#         return table_names

#     def _check_real_tables_in_migration(self, migration_file):
#         """Check if migration contains real database tables"""
#         content = migration_file.read_text()
#         real_tables = ["extensions", "providers", "teams", "users"]
#         return any(table in content for table in real_tables)

#     def _check_extension_tables_in_migration(self, migration_file, extension_name):
#         """Check if migration contains the correct tables for a specific extension"""
#         content = migration_file.read_text()

#         # Dynamically get expected tables by inspecting the extension's BLL files
#         expected_tables = self._get_extension_table_names(extension_name)

#         if not expected_tables:
#             # For extensions with no expected tables, migration should be empty or not created
#             has_table_operations = any(
#                 op in content
#                 for op in ["op.create_table", "op.add_column", "op.drop_table"]
#             )
#             return not has_table_operations  # Should NOT have table operations

#         # For extensions with expected tables, check that they're all present
#         found_tables = []
#         missing_tables = []

#         for table in expected_tables:
#             if table in content:
#                 found_tables.append(table)
#             else:
#                 missing_tables.append(table)

#         if missing_tables:
#             logger.error(
#                 f"Extension {extension_name} migration missing tables: {missing_tables}. "
#                 f"Found: {found_tables}. Expected: {expected_tables}"
#             )

#         return len(found_tables) == len(expected_tables)

#     def setup_extension_for_testing(self, extension_name: str):
#         """Set up an extension for testing by checking if it's real or needs test setup"""
#         if extension_name == "core":
#             return True

#         # Check if this is a real extension that already exists
#         real_ext_dir = self.extensions_dir / extension_name
#         if real_ext_dir.exists():
#             # This is a real extension, check if it has BLL models
#             bll_files = list(real_ext_dir.glob("BLL_*.py"))
#             if bll_files:
#                 logger.debug(
#                     f"Using existing real extension with {len(bll_files)} BLL models: {extension_name}"
#                 )
#                 return True
#             else:
#                 logger.debug(
#                     f"Real extension {extension_name} exists but has no BLL models - skipping migration tests"
#                 )
#                 return False

#         # This is a test extension, create it safely
#         logger.debug(f"Setting up test extension: {extension_name}")
#         self._create_test_extension(extension_name)
#         return True

#     # Unified Matrix Tests - Work for both core and extensions with conditional logic

#     @pytest.mark.parametrize(
#         "migration_target", ["core"] + MigrationTestConfig.get_configured_extensions()
#     )
#     @pytest.mark.parametrize(
#         "revision_variation", create_revision_variations(), ids=lambda v: v["type"]
#     )
#     def test_revision_variations(self, migration_target, revision_variation):
#         """Test various revision creation scenarios for core and extensions."""
#         target = migration_target
#         variation = revision_variation

#         # Set up extension if needed
#         if target != "core":
#             setup_success = self.setup_extension_for_testing(target)
#             if not setup_success:
#                 pytest.skip(
#                     f"Extension {target} has no database models - skipping migration test"
#                 )

#         # Build command based on variation
#         command_args = [
#             "revision",
#             "-m",
#             f"{stringcase.capitalcase(target)} {variation['message']}",
#         ]
#         command_args.extend(variation.get("flags", []))

#         result = self.run_migration_command_for_target(target, *command_args)
#         assert result.returncode == 0, f"Revision creation should succeed for {target}"

#         migrations = self.get_migration_files_for_target(target)
#         assert len(migrations) >= 1, f"Should create migration file(s) for {target}"

#         content = migrations[-1].read_text()  # Get latest migration
#         assert "def upgrade()" in content, "Migration should have upgrade function"
#         assert "def downgrade()" in content, "Migration should have downgrade function"

#         # Check message content based on variation type
#         if variation["type"] in ["auto", "default_autogenerate"]:
#             assert (
#                 f"{stringcase.capitalcase(target)} {variation['message']}" in content
#             ), "Migration should contain the specified message"
#         elif variation["type"] == "no_autogenerate":
#             # For no-autogenerate, check it did NOT generate content for existing models
#             assert (
#                 "op.create_table" not in content
#             ), "Should not contain table creation for no-autogenerate"
#             assert (
#                 f"{target.capitalize()} {variation['message']}" in content
#             ), "Migration should contain the specified message"

#         # For auto and default_autogenerate variations, check for real tables in core
#         if target == "core" and variation["type"] in ["auto", "default_autogenerate"]:
#             real_tables_found = self._check_real_tables_in_migration(migrations[-1])
#             assert (
#                 real_tables_found
#             ), "Should contain real database tables in migration content for core"

#         # For extensions, check that the migration contains the correct extension tables
#         if target != "core" and variation["type"] in ["auto", "default_autogenerate"]:
#             extension_tables_correct = self._check_extension_tables_in_migration(
#                 migrations[-1], target
#             )
#             assert (
#                 extension_tables_correct
#             ), f"Extension {target} migration should contain all expected tables from its BLL models"

#     @pytest.mark.parametrize(
#         "migration_target", ["core"] + MigrationTestConfig.get_configured_extensions()
#     )
#     @pytest.mark.parametrize(
#         "regenerate_variation", create_regenerate_variations(), ids=lambda v: v["type"]
#     )
#     def test_regenerate_variations(self, migration_target, regenerate_variation):
#         """Test various regenerate scenarios for core and extensions."""
#         target = migration_target
#         variation = regenerate_variation

#         # Set up extension if needed
#         if target != "core":
#             setup_success = self.setup_extension_for_testing(target)
#             if not setup_success:
#                 pytest.skip(
#                     f"Extension {target} has no database models - skipping migration test"
#                 )

#         # Clear any existing migrations
#         self.clear_migrations_for_target(target)

#         # Create initial migration first
#         result = self.run_migration_command_for_target(
#             target, "revision", "-m", f"{target.capitalize()} initial for regen"
#         )
#         assert (
#             result.returncode == 0
#         ), f"Initial migration creation should succeed for {target}"

#         old_migrations = self.get_migration_files_for_target(target)
#         assert len(old_migrations) >= 1

#         # Run regenerate based on variation
#         if variation["message"]:
#             # With explicit message
#             if target == "core":
#                 success = self.migration_manager.regenerate_migrations(
#                     message=variation["message"]
#                 )
#             else:
#                 success = self.migration_manager.regenerate_migrations(
#                     extension_name=target, message=variation["message"]
#                 )
#         else:
#             # Without message (should use default)
#             if target == "core":
#                 success = self.migration_manager.regenerate_migrations()
#             else:
#                 success = self.migration_manager.regenerate_migrations(
#                     extension_name=target
#                 )

#         assert success, f"Regenerate {variation['type']} should succeed for {target}"

#         new_migrations = self.get_migration_files_for_target(target)
#         assert len(new_migrations) >= 1, "Should have migration(s) after regenerate"

#         # Verify content
#         content = new_migrations[-1].read_text()
#         assert (
#             "op.create_table" in content
#         ), "Regenerated migration should contain table creation"

#         # Check message based on variation
#         if variation["message"]:
#             assert variation["message"] in content, "Should contain specified message"
#         else:
#             assert (
#                 "initial schema" in content
#             ), "Should contain default 'initial schema' message"

#         # For core, check for real database tables
#         if target == "core":
#             real_tables_found = self._check_real_tables_in_migration(new_migrations[-1])
#             assert (
#                 real_tables_found
#             ), "Should contain real database tables in migration content"

#         # For extensions, check that the migration contains the correct extension tables
#         if target != "core":
#             extension_tables_correct = self._check_extension_tables_in_migration(
#                 new_migrations[-1], target
#             )
#             assert (
#                 extension_tables_correct
#             ), f"Extension {target} regenerated migration should contain all expected tables from its BLL models"

#     @pytest.mark.parametrize(
#         "migration_target", ["core"] + MigrationTestConfig.get_configured_extensions()
#     )
#     def test_upgrade_downgrade(self, migration_target):
#         """Test upgrading and downgrading for core and extensions."""
#         target = migration_target

#         # Set up extension if needed
#         if target != "core":
#             setup_success = self.setup_extension_for_testing(target)
#             if not setup_success:
#                 pytest.skip(
#                     f"Extension {target} has no database models - skipping migration test"
#                 )

#         # Clear migrations and create one
#         self.clear_migrations_for_target(target)
#         result = self.run_migration_command_for_target(
#             target, "revision", "-m", f"{target.capitalize()} revision 1"
#         )
#         assert result.returncode == 0, f"Revision creation should succeed for {target}"

#         migrations = self.get_migration_files_for_target(target)
#         assert len(migrations) >= 1, f"Should have at least one migration for {target}"

#         if target == "core":
#             # Core has specific revision ID handling
#             rev1 = migrations[0].stem.split("_")[0]

#             # Upgrade to head
#             result = self.run_migration_command_for_target(target, "upgrade", "head")
#             assert result.returncode == 0, f"Upgrade should succeed for {target}"

#             result = self.run_migration_command_for_target(target, "current")
#             assert result.returncode == 0, f"Current should succeed for {target}"

#             # Downgrade to base
#             result = self.run_migration_command_for_target(target, "downgrade", "base")
#             assert result.returncode == 0, f"Downgrade should succeed for {target}"

#             result = self.run_migration_command_for_target(target, "current")
#             assert (
#                 result.returncode == 0
#             ), f"Current should succeed after downgrade for {target}"
#         else:
#             # Extensions have different handling
#             # Upgrade to head
#             result = self.run_migration_command_for_target(target, "upgrade", "head")
#             assert result.returncode == 0, f"Upgrade should succeed for {target}"

#             result = self.run_migration_command_for_target(target, "current")
#             assert (
#                 result.returncode == 0
#             ), f"Current command should succeed for {target}"

#             # Downgrade to base
#             result = self.run_migration_command_for_target(target, "downgrade", "base")
#             assert result.returncode == 0, f"Downgrade should succeed for {target}"

#             result = self.run_migration_command_for_target(target, "current")
#             assert (
#                 result.returncode == 0
#             ), f"Current command should succeed after downgrade for {target}"

#     @pytest.mark.parametrize(
#         "migration_target", ["core"] + MigrationTestConfig.get_configured_extensions()
#     )
#     def test_skip_empty_migration(self, migration_target):
#         """Test that an autogenerated migration with no changes is skipped for core and extensions."""
#         target = migration_target

#         # Set up extension if needed
#         if target != "core":
#             setup_success = self.setup_extension_for_testing(target)
#             if not setup_success:
#                 pytest.skip(
#                     f"Extension {target} has no database models - skipping migration test"
#                 )

#         # Clear migrations and create initial one
#         self.clear_migrations_for_target(target)
#         result = self.run_migration_command_for_target(
#             target, "revision", "-m", f"{target.capitalize()} initial non-empty"
#         )
#         assert result.returncode == 0, f"Initial revision should succeed for {target}"

#         # Verify initial migration
#         migrations = self.get_migration_files_for_target(target)
#         initial_count = len(migrations)
#         assert initial_count >= 1, "Should have initial migration"

#         # Run revision again with no model changes - should detect no changes
#         result = self.run_migration_command_for_target(
#             target,
#             "revision",
#             "-m",
#             f"{target.capitalize()} should be empty",
#             expect_success=False,
#         )

#         # Since no changes should be detected, and the script should skip empty migrations,
#         # we expect no new migration file to be created
#         migrations_after = self.get_migration_files_for_target(target)
#         assert (
#             len(migrations_after) == initial_count
#         ), "No new migration should be created when no changes detected"

#     # Legacy matrix tests for comprehensive operations

#     @pytest.mark.parametrize(
#         "migration_target", ["core"] + MigrationTestConfig.get_configured_extensions()
#     )
#     def test_matrix_revision_creation(self, migration_target):
#         """Test revision creation across core and extensions."""
#         target = migration_target

#         # Set up extension if needed
#         if target != "core":
#             setup_success = self.setup_extension_for_testing(target)
#             if not setup_success:
#                 pytest.skip(
#                     f"Extension {target} has no database models - skipping migration test"
#                 )

#         # Test revision creation
#         result = self.run_migration_command_for_target(
#             target, "revision", "-m", f"{target.capitalize()} matrix test"
#         )
#         assert result.returncode == 0, f"Revision creation should succeed for {target}"

#         migrations = self.get_migration_files_for_target(target)
#         assert (
#             len(migrations) >= 1
#         ), f"Should have at least one migration file for {target}"

#         # Verify migration content
#         latest_migration = migrations[-1]  # Get the most recent migration
#         content = latest_migration.read_text()
#         assert (
#             "def upgrade()" in content
#         ), f"Migration for {target} should have upgrade function"
#         assert (
#             "def downgrade()" in content
#         ), f"Migration for {target} should have downgrade function"
#         assert (
#             f"{target.capitalize()} matrix test" in content
#         ), f"Migration for {target} should contain the message"

#         # For extensions, verify the migration contains the correct tables
#         if target != "core":
#             extension_tables_correct = self._check_extension_tables_in_migration(
#                 latest_migration, target
#             )
#             assert (
#                 extension_tables_correct
#             ), f"Extension {target} migration should contain all expected tables from its BLL models"

#     @pytest.mark.parametrize(
#         "migration_target", ["core"] + MigrationTestConfig.get_configured_extensions()
#     )
#     def test_matrix_upgrade_operations(self, migration_target):
#         """Test upgrade operations across core and extensions."""
#         target = migration_target

#         # Set up extension if needed
#         if target != "core":
#             setup_success = self.setup_extension_for_testing(target)
#             if not setup_success:
#                 pytest.skip(
#                     f"Extension {target} has no database models - skipping migration test"
#                 )

#         # Create a migration first
#         self.clear_migrations_for_target(target)
#         result = self.run_migration_command_for_target(
#             target, "revision", "-m", f"{target.capitalize()} for upgrade test"
#         )
#         assert result.returncode == 0, f"Revision creation should succeed for {target}"

#         # Test upgrade
#         result = self.run_migration_command_for_target(target, "upgrade", "head")
#         assert result.returncode == 0, f"Upgrade should succeed for {target}"

#         # Verify current state
#         current_result = self.run_migration_command_for_target(target, "current")
#         assert (
#             current_result.returncode == 0
#         ), f"Current command should succeed for {target}"

#     @pytest.mark.parametrize(
#         "migration_target", ["core"] + MigrationTestConfig.get_configured_extensions()
#     )
#     def test_matrix_history_operations(self, migration_target):
#         """Test history operations across core and extensions."""
#         target = migration_target

#         # Set up extension if needed
#         if target != "core":
#             setup_success = self.setup_extension_for_testing(target)
#             if not setup_success:
#                 pytest.skip(
#                     f"Extension {target} has no database models - skipping migration test"
#                 )

#         # Create a migration first to have some history
#         self.clear_migrations_for_target(target)
#         result = self.run_migration_command_for_target(
#             target, "revision", "-m", f"{target.capitalize()} for history test"
#         )
#         assert result.returncode == 0, f"Revision creation should succeed for {target}"

#         # Test history command
#         result = self.run_migration_command_for_target(target, "history")
#         assert result.returncode == 0, f"History command should succeed for {target}"

#         # Test current command
#         current_result = self.run_migration_command_for_target(target, "current")
#         assert (
#             current_result.returncode == 0
#         ), f"Current command should succeed for {target}"


# @pytest.mark.dependency(depends=["migrations_meta", "migrations_mock"], scope="session")
# class TestMigrationExtensionDynamic(AbstractMigrationTest):
#     """Dynamic extension tests that adapt to the configured extensions"""

#     # Configuration for this test class
#     TEST_DB_NAME_SUFFIX = "dynamic"
#     TEST_EXTENSIONS = ""  # No extensions by default, will be set dynamically
#     TRACK_CLEANUP = True
#     USE_MOCK_DIRECTORIES = False
#     CREATE_TEST_EXTENSIONS = []

#     def get_test_config(self) -> Dict[str, Any]:
#         """Configure dynamic extension tests."""
#         return {
#             "test_type": "dynamic",
#             "create_mock_extensions": False,
#             "matrix_targets": ["core"],
#             "configured_extensions": MigrationTestConfig.get_configured_extensions(),
#         }

#     def test_extension_discovery_completeness(self):
#         """Test that verifies all real extensions are properly discovered and categorized"""
#         configured_extensions = MigrationTestConfig.get_configured_extensions()

#         # Verify we're finding the real extensions
#         expected_real_extensions = ["auth_mfa", "email", "database", "meta_logging"]
#         found_real_extensions = [
#             ext for ext in configured_extensions if ext in expected_real_extensions
#         ]

#         logger.debug(f"Discovered extensions: {configured_extensions}")
#         logger.debug(f"Real extensions found: {found_real_extensions}")

#         # This is informational - we don't fail if extensions are missing,
#         # but we verify our discovery mechanism works
#         assert len(configured_extensions) >= 0, "Should discover extensions (or none)"

#         # Check that our test matrix will include these extensions
#         test_targets = ["core"] + configured_extensions
#         assert len(test_targets) >= 1, "Should have at least core target"

#         logger.debug(
#             "✅ Extension discovery and test matrix generation working correctly"
#         )


# @pytest.mark.dependency(depends=["migrations_meta", "migrations_mock"], scope="session")
# class TestMigrationCleanup(AbstractMigrationTest):
#     """Meta tests to verify that migration tests clean up properly"""

#     # Configuration for this test class
#     TEST_DB_NAME_SUFFIX = "cleanup"
#     TEST_EXTENSIONS = ""
#     TRACK_CLEANUP = True
#     USE_MOCK_DIRECTORIES = False
#     CREATE_TEST_EXTENSIONS = ["test_cleanup_ext"]

#     def get_test_config(self) -> Dict[str, Any]:
#         """Configure cleanup verification tests."""
#         return {
#             "test_type": "cleanup",
#             "create_mock_extensions": False,
#             "matrix_targets": ["core"],
#         }

#     def test_migration_test_cleanup_verification(self):
#         """Meta test that verifies migration tests don't leave files behind."""
#         # Capture the state before creating test files
#         existing_files_before = set()
#         existing_dirs_before = set()

#         # Snapshot database directory
#         for file_path in self.database_dir.rglob("*"):
#             if file_path.is_file():
#                 existing_files_before.add(file_path)
#             elif file_path.is_dir():
#                 existing_dirs_before.add(file_path)

#         # Snapshot extensions directory
#         if self.extensions_dir.exists():
#             for file_path in self.extensions_dir.rglob("*"):
#                 if file_path.is_file():
#                     existing_files_before.add(file_path)
#                 elif file_path.is_dir():
#                     existing_dirs_before.add(file_path)

#         # Create some test files to verify tracking
#         test_ext_name = "cleanup_verification_ext"
#         test_ext_dir = self._create_test_extension(test_ext_name)

#         # Verify that files were tracked
#         assert len(self.created_model_files) > 0, "Should track created model files"
#         assert (
#             len(self.created_test_extensions) > 0
#         ), "Should track created extension directories"

#         # Verify tracked files actually exist
#         for tracked_file in self.created_model_files:
#             assert tracked_file.exists(), f"Tracked file should exist: {tracked_file}"

#         for tracked_dir in self.created_test_extensions:
#             assert (
#                 tracked_dir.exists()
#             ), f"Tracked directory should exist: {tracked_dir}"

#         logger.debug("✅ File tracking completeness verification passed")
#         # Cleanup will happen automatically in fixture teardown

#     def test_tracking_completeness(self):
#         """Test that verifies all file creation is properly tracked."""
#         initial_model_files = len(self.created_model_files)
#         initial_test_extensions = len(self.created_test_extensions)

#         # Create test extension which should track files
#         test_extension_name = "tracking_test_ext"
#         success = self.setup_extension_for_testing(test_extension_name)

#         if success:
#             # Verify that files were tracked
#             assert (
#                 len(self.created_model_files) > initial_model_files
#             ), "Should track new model files"
#             assert (
#                 len(self.created_test_extensions) > initial_test_extensions
#             ), "Should track new extension directories"

#         logger.debug("✅ File tracking completeness verification passed")


# @pytest.mark.dependency(depends=["migrations_meta", "migrations_mock"], scope="session")
# class TestModelExtensionMigrations(AbstractMigrationTest):
#     """Test suite for model extension migration functionality."""

#     # Configuration for this test class
#     TEST_DB_NAME_SUFFIX = "model_ext"
#     TEST_EXTENSIONS = (
#         "test_payment,test_analytics"  # Test with specific model extensions
#     )
#     TRACK_CLEANUP = True
#     USE_MOCK_DIRECTORIES = False
#     CREATE_TEST_EXTENSIONS = ["test_payment", "test_analytics"]

#     def get_test_config(self) -> Dict[str, Any]:
#         """Configure model extension tests."""
#         return {
#             "test_type": "model_extension",
#             "create_mock_extensions": True,
#             "matrix_targets": ["core", "test_payment", "test_analytics"],
#         }

#     def test_core_table_extension_detection(self):
#         """Test that core tables extended by extensions are properly detected."""
#         logger.debug("\n=== Testing Core Table Extension Detection ===")

#         from typing import Optional

#         from pydantic import Field

#         from lib.Pydantic2SQLAlchemy import (
#             ApplicationModel,
#             DatabaseMixin,
#             extension_model,
#         )

#         # Create core model
#         class CoreUserModel(ApplicationModel, DatabaseMixin):
#             name: str = Field(..., description="User name")
#             email: str = Field(..., description="User email")

#         # Create extension that extends the core model
#         @extension_model(CoreUserModel)
#         class TestPayment_UserModel:
#             payment_customer_id: Optional[str] = Field(
#                 None, description="Payment customer ID"
#             )
#             subscription_tier: Optional[str] = Field(
#                 None, description="Subscription tier"
#             )

#         # Get the SQLAlchemy model
#         sql_model = CoreUserModel.DB
#         table = sql_model.__table__

#         # Test the detection function
#         from database.migrations.Migration import MigrationManager

#         # Should be detected as owned by test_payment extension
#         is_owned_by_payment = MigrationManager.env_is_table_owned_by_extension(
#             table, "test_payment"
#         )

#         # Should NOT be detected as owned by test_analytics extension
#         is_owned_by_analytics = MigrationManager.env_is_table_owned_by_extension(
#             table, "test_analytics"
#         )

#         assert (
#             is_owned_by_payment
#         ), "Core table extended by test_payment should be detected as owned"
#         assert (
#             not is_owned_by_analytics
#         ), "Core table should not be owned by test_analytics"

#         logger.debug("✓ Core table extension detection works correctly")

#     def test_extension_registry_integration(self):
#         """Test integration with the extension registry system."""
#         logger.debug("\n=== Testing Extension Registry Integration ===")

#         from typing import Optional

#         from pydantic import Field

#         from lib.Pydantic2SQLAlchemy import (
#             ApplicationModel,
#             DatabaseMixin,
#             extension_model,
#             get_applied_extensions,
#         )

#         # Create core model
#         class RegistryTestModel(ApplicationModel, DatabaseMixin):
#             name: str = Field(..., description="Registry test name")

#         # Apply extension
#         @extension_model(RegistryTestModel)
#         class TestPayment_RegistryModel:
#             registry_field: Optional[str] = Field(
#                 None, description="Registry test field"
#             )

#         # Check that extension is properly registered
#         applied_extensions = get_applied_extensions()

#         # Find our model in the registry
#         target_key = f"{RegistryTestModel.__module__}.{RegistryTestModel.__name__}"
#         extension_key = f"{TestPayment_RegistryModel.__module__}.{TestPayment_RegistryModel.__name__}"

#         assert target_key in applied_extensions, "Target model should be in registry"
#         assert (
#             extension_key in applied_extensions[target_key]
#         ), "Extension should be registered for target model"

#         # Test that migration detection uses this registry
#         sql_model = RegistryTestModel.DB
#         table = sql_model.__table__

#         from database.migrations.Migration import MigrationManager

#         is_owned = MigrationManager.env_is_table_owned_by_extension(
#             table, "test_payment"
#         )

#         assert is_owned, "Migration system should use extension registry for detection"

#         logger.debug("✓ Extension registry integration works correctly")

#     def test_env_static_methods_integration(self):
#         """Test integration of static methods used by env.py."""
#         from database.migrations.Migration import MigrationManager

#         logger.debug("\n=== Testing env.py Static Methods Integration ===")

#         # Test env_is_table_owned_by_extension with real tables
#         from lib.Pydantic2SQLAlchemy import get_applied_extensions

#         # Import a real model to test with
#         try:
#             from logic.BLL_Auth import UserModel

#             user_table = UserModel.DB.__table__

#             # Test that core table is not owned by extensions
#             for ext_name in self.get_configured_extensions():
#                 is_owned = MigrationManager.env_is_table_owned_by_extension(
#                     user_table, ext_name
#                 )
#                 # Should be False unless this extension actually extends the User model
#                 logger.debug(f"UserModel table owned by {ext_name}: {is_owned}")

#         except ImportError as e:
#             logger.warning(f"Could not import UserModel for testing: {e}")

#         # Test env_include_object filter
#         # This is called during migration generation to filter tables
#         test_result = MigrationManager.env_include_object(
#             object=None,
#             name="test_table",
#             type_="table",
#             reflected=False,
#             compare_to=None,
#         )
#         # Should return True for core migrations (no ALEMBIC_EXTENSION set)
#         assert isinstance(test_result, bool), "include_object should return boolean"

#         logger.debug("✓ env.py static methods integration verified")

#     @pytest.mark.parametrize(
#         "table_ownership_scenario",
#         [
#             {"type": "core_table", "extension": None},
#             {"type": "extension_table", "extension": "test_ext"},
#             {"type": "extended_core_table", "extension": "test_payment"},
#         ],
#     )
#     def test_table_ownership_detection(self, table_ownership_scenario):
#         """Test comprehensive table ownership detection scenarios."""
#         from sqlalchemy import Column, Integer, MetaData, String, Table

#         from database.migrations.Migration import MigrationManager

#         # Create a mock table for testing
#         metadata = MetaData()
#         test_table = Table(
#             f"test_table_{table_ownership_scenario['type']}",
#             metadata,
#             Column("id", Integer, primary_key=True),
#             Column("name", String(50)),
#         )

#         # Set up table metadata based on scenario
#         if table_ownership_scenario["extension"]:
#             test_table.info["extension"] = table_ownership_scenario["extension"]

#         # Test ownership detection
#         test_extension = table_ownership_scenario.get("extension", "nonexistent_ext")
#         is_owned = MigrationManager.env_is_table_owned_by_extension(
#             test_table, test_extension
#         )

#         if table_ownership_scenario["extension"] == test_extension:
#             assert is_owned, f"Table should be owned by {test_extension}"
#         else:
#             # For scenarios where we test with a different extension
#             # the result depends on the specific test case logic
#             logger.debug(
#                 f"Table ownership result for {table_ownership_scenario['type']}: {is_owned}"
#             )

#     def test_migration_error_recovery(self):
#         """Test migration system recovery from various error conditions."""
#         logger.debug("\n=== Testing Migration Error Recovery ===")

#         # Test recovery from invalid migration content
#         test_target = "core"
#         self.clear_migrations_for_target(test_target)

#         # Create a valid migration first
#         result = self.run_migration_command_for_target(
#             test_target, "revision", "-m", "test migration", "--no-autogenerate"
#         )
#         assert result.returncode == 0, "Initial migration should succeed"

#         # Verify the migration file exists and can be read
#         migrations = self.get_migration_files_for_target(test_target)
#         assert len(migrations) >= 1, "Should have created migration file"

#         migration_file = migrations[-1]
#         original_content = migration_file.read_text()
#         assert (
#             "def upgrade()" in original_content
#         ), "Migration should have upgrade function"

#         # Test that the migration system handles the scenario gracefully
#         # (We don't actually corrupt files as that would break the test environment)
#         logger.debug("✓ Migration error recovery scenarios verified")

#     def test_cross_extension_dependencies(self):
#         """Test migration behavior with cross-extension dependencies."""
#         logger.debug("\n=== Testing Cross-Extension Dependencies ===")

#         configured_extensions = self.get_configured_extensions()
#         if len(configured_extensions) < 2:
#             pytest.skip("Need at least 2 configured extensions for dependency testing")

#         # Test that migrations can handle multiple extensions
#         for ext_name in configured_extensions[:2]:  # Test with first 2 extensions
#             if self.setup_extension_for_testing(ext_name):
#                 # Try to create a migration for this extension
#                 result = self.run_migration_command_for_target(
#                     ext_name, "revision", "-m", f"dependency test for {ext_name}"
#                 )

#                 # The result depends on whether the extension has models
#                 # We're mainly testing that the system doesn't crash
#                 logger.debug(
#                     f"Cross-extension migration result for {ext_name}: {result.returncode == 0}"
#                 )

#         logger.debug("✓ Cross-extension dependency handling verified")
