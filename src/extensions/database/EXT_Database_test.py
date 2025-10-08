"""
Tests for EXT_Database extension.
Tests static extension functionality with Provider Rotation System.
"""

from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from extensions.AbstractEXTTest import (
    ExtensionServerMixin,
    ExtensionTestConfig,
    ExtensionTestType,
)
from extensions.database.EXT_Database import (
    EXT_Database,
    AbstractDatabaseExtensionProvider,
)
from lib.Dependencies import Dependencies, PIP_Dependency


class ConcreteDatabaseProvider(AbstractDatabaseExtensionProvider):
    """Concrete implementation of AbstractDatabaseExtensionProvider for testing"""

    # Static provider metadata
    name = "test_database"
    friendly_name = "Test Database Provider"
    description = "Test database provider for unit tests"
    db_type = "test"

    # Environment variables for testing
    _env = {
        "TEST_DATABASE_URL": "test://localhost:1234/testdb",
        "TEST_DATABASE_TOKEN": "test_token",
    }

    # Test abilities
    _abilities = {
        "database",
        "sql",
        "data_storage",
        "test_ability",
    }

    # Link to parent extension (REQUIRED for Provider Rotation System)
    extension = EXT_Database

    @classmethod
    def bond_instance(cls, config: Dict[str, any]) -> None:
        """Configure the test provider"""
        cls._config = config

    @classmethod
    async def execute_sql(cls, query: str, **kwargs) -> str:
        """Mock SQL execution"""
        return f"Test SQL executed: {query}"

    @classmethod
    async def get_schema(cls, **kwargs) -> str:
        """Mock schema retrieval"""
        return "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);"

    @classmethod
    async def chat_with_db(cls, request: str, **kwargs) -> str:
        """Mock database chat"""
        return f"Test chat response for: {request}"

    @classmethod
    async def execute_query(cls, query: str, **kwargs) -> str:
        """Mock query execution"""
        return f"Test query executed: {query}"

    @classmethod
    async def write_data(cls, data: str, **kwargs) -> str:
        """Mock data writing"""
        return f"Test data written: {data}"

    @classmethod
    def validate_config(cls) -> List[str]:
        """Mock configuration validation"""
        return []  # No issues for test provider


class TestEXTDatabase(ExtensionServerMixin):
    """
    Test suite for EXT_Database extension.
    Tests static extension functionality with Provider Rotation System.
    """

    # Extension configuration for ExtensionServerMixin
    extension_class = EXT_Database

    # Test configuration
    test_config = ExtensionTestConfig(
        test_types={
            ExtensionTestType.STRUCTURE,
            ExtensionTestType.METADATA,
            ExtensionTestType.DEPENDENCIES,
            ExtensionTestType.ABILITIES,
            ExtensionTestType.ENVIRONMENT,
            ExtensionTestType.ROTATION,
        },
        expected_abilities={
            "database_query",
            "database_schema",
            "database_chat",
            "sql_execution",
            "data_storage",
            "relational_db",
            "nosql_db",
            "time_series_db",
        },
        expected_env_vars={
            "DATABASE_TYPE": "sqlite",
            "DATABASE_HOST": "",
            "DATABASE_PORT": "",
            "DATABASE_NAME": "",
            "DATABASE_USERNAME": "",
            "DATABASE_PASSWORD": "",
            "DATABASE_FILE": "",
            "INFLUXDB_VERSION": "2",
            "INFLUXDB_ORG": "",
            "INFLUXDB_TOKEN": "",
            "INFLUXDB_BUCKET": "",
        },
    )

    def test_extension_metadata(self):
        """Test static extension metadata"""
        assert EXT_Database.name == "database"
        assert EXT_Database.friendly_name == "Database Connectivity"
        assert EXT_Database.version == "1.0.0"
        assert "database connectivity" in EXT_Database.description.lower()

    def test_provider_discovery(self):
        """Test provider auto-discovery mechanism"""
        # Test that provider discovery works through filesystem scanning
        # Clear the cache to force re-discovery
        EXT_Database._providers = []

        providers = EXT_Database.providers
        assert isinstance(providers, list)
        # The actual providers discovered depend on what PRV_*.py files exist
        # in the database extension directory

    def test_get_abilities(self):
        """Test ability aggregation from extension and providers"""
        with patch.object(
            EXT_Database, "providers", return_value=[ConcreteDatabaseProvider]
        ):
            abilities = EXT_Database.get_abilities()

            # Should include extension abilities
            for ability in EXT_Database._abilities:
                assert ability in abilities

            # Should include provider abilities
            for ability in ConcreteDatabaseProvider._abilities:
                assert ability in abilities

    def test_has_ability(self):
        """Test ability checking"""
        with patch.object(
            EXT_Database, "providers", return_value=[ConcreteDatabaseProvider]
        ):
            assert EXT_Database.has_ability("database_query")
            assert EXT_Database.has_ability("sql_execution")
            assert EXT_Database.has_ability("test_ability")  # From test provider
            assert not EXT_Database.has_ability("nonexistent_ability")

    def test_get_database_classifications(self):
        """Test database type classifications"""
        # Test all classifications
        all_classifications = EXT_Database.get_database_classifications()
        assert "relational" in all_classifications
        assert "document" in all_classifications
        assert "time_series" in all_classifications
        assert "graph" in all_classifications

        # Test specific database type
        postgres_classifications = EXT_Database.get_database_classifications("postgres")
        assert "relational" in postgres_classifications
        assert postgres_classifications["relational"] == ["postgres"]

    def test_get_default_port(self):
        """Test default port assignment"""
        assert EXT_Database.get_default_port("postgres") == 5432
        assert EXT_Database.get_default_port("mysql") == 3306
        assert EXT_Database.get_default_port("mongodb") == 27017
        assert EXT_Database.get_default_port("influxdb") == 8086
        assert EXT_Database.get_default_port("sqlite") == 0
        assert EXT_Database.get_default_port("unknown") == 0

    def test_get_provider_names(self):
        """Test provider name discovery"""
        with patch.object(
            EXT_Database, "providers", return_value=[ConcreteDatabaseProvider]
        ):
            provider_names = EXT_Database.get_provider_names()
            assert "test_database" in provider_names

    def test_validate_config_no_providers(self):
        """Test configuration validation with no providers"""
        with patch.object(EXT_Database, "providers", return_value=[]):
            issues = EXT_Database.validate_config()
            assert len(issues) > 0
            assert any(
                "no database providers available" in issue.lower() for issue in issues
            )

    def test_validate_config_with_providers(self):
        """Test configuration validation with providers"""
        with patch.object(
            EXT_Database, "providers", return_value=[ConcreteDatabaseProvider]
        ):
            issues = EXT_Database.validate_config()
            # Should delegate to provider validation
            assert isinstance(issues, list)

    @pytest.mark.asyncio
    async def test_execute_sql_static_method(self):
        """Test static SQL execution via rotation system"""
        with patch.object(EXT_Database, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value="SQL executed successfully")

            result = await EXT_Database.execute_sql("SELECT * FROM test")

            assert result == "SQL executed successfully"
            mock_root.rotate.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_schema_static_method(self):
        """Test static schema retrieval via rotation system"""
        with patch.object(EXT_Database, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value="CREATE TABLE test (id INTEGER);")

            result = await EXT_Database.get_schema()

            assert "CREATE TABLE" in result
            mock_root.rotate.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_db_static_method(self):
        """Test static database chat via rotation system"""
        with patch.object(EXT_Database, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value="Chat response")

            result = await EXT_Database.chat_with_db("Show me all users")

            assert result == "Chat response"
            mock_root.rotate.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_static_method(self):
        """Test static query execution via rotation system"""
        with patch.object(EXT_Database, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value="Query executed")

            result = await EXT_Database.execute_query(
                "FROM bucket |> range(start: -1h)"
            )

            assert result == "Query executed"
            mock_root.rotate.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_data_static_method(self):
        """Test static data writing via rotation system"""
        with patch.object(EXT_Database, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value="Data written")

            result = await EXT_Database.write_data(
                '{"measurement": "test", "value": 1}'
            )

            assert result == "Data written"
            mock_root.rotate.assert_called_once()

    def test_required_permissions(self):
        """Test required permissions list"""
        permissions = EXT_Database.get_required_permissions()

        assert isinstance(permissions, list)
        assert "database:query" in permissions
        assert "database:schema" in permissions
        assert "database:write" in permissions
        assert "database:admin" in permissions

    def test_env_property(self):
        """Test environment variable property"""
        env_vars = EXT_Database.env

        assert isinstance(env_vars, dict)
        assert "DATABASE_TYPE" in env_vars
        assert "DATABASE_HOST" in env_vars
        assert "INFLUXDB_TOKEN" in env_vars

    def test_dependency_properties(self):
        """Test dependency property access"""
        pip_deps = EXT_Database.pip_dependencies
        ext_deps = EXT_Database.ext_dependencies
        sys_deps = EXT_Database.sys_dependencies

        assert isinstance(pip_deps, list)
        assert isinstance(ext_deps, list)
        assert isinstance(sys_deps, list)

        # Should have database-related dependencies
        pip_names = [dep.name for dep in pip_deps]
        assert "psycopg2-binary" in pip_names
        assert "pymongo" in pip_names
        assert "influxdb" in pip_names

    def test_startup_shutdown_hooks(self):
        """Test startup and shutdown hooks"""
        with patch("lib.Logging.logger") as mock_logger:
            # Test startup
            EXT_Database.on_startup()
            mock_logger.debug.assert_called()

            # Test shutdown
            EXT_Database.on_shutdown()
            mock_logger.debug.assert_called()


class TestAbstractDatabaseExtensionProvider:
    """Test the abstract database extension provider base class"""

    def test_concrete_provider_implementation(self):
        """Test that concrete provider implements required methods"""
        # Verify all abstract methods are implemented
        provider = ConcreteDatabaseProvider

        assert hasattr(provider, "bond_instance")
        assert hasattr(provider, "execute_sql")
        assert hasattr(provider, "get_schema")
        assert hasattr(provider, "chat_with_db")

        # Test metadata
        assert provider.name == "test_database"
        assert provider.db_type == "test"
        assert provider.extension == EXT_Database

    def test_provider_abilities(self):
        """Test provider ability management"""
        abilities = ConcreteDatabaseProvider.get_abilities()

        assert isinstance(abilities, set)
        assert "database" in abilities
        assert "sql" in abilities
        assert "test_ability" in abilities

    def test_provider_info(self):
        """Test provider information retrieval"""
        info = ConcreteDatabaseProvider.get_provider_info()

        assert info["name"] == "test_database"
        assert info["friendly_name"] == "Test Database Provider"
        assert info["type"] == "test"
        assert isinstance(info["abilities"], list)

    @pytest.mark.asyncio
    async def test_provider_methods(self):
        """Test provider method implementations"""
        # Test SQL execution
        result = await ConcreteDatabaseProvider.execute_sql("SELECT 1")
        assert "Test SQL executed" in result

        # Test schema retrieval
        schema = await ConcreteDatabaseProvider.get_schema()
        assert "CREATE TABLE" in schema

        # Test chat
        chat_response = await ConcreteDatabaseProvider.chat_with_db("test request")
        assert "Test chat response" in chat_response

    def test_provider_metadata_attributes(self):
        """Test that provider has required metadata attributes"""
        assert hasattr(ConcreteDatabaseProvider, "name")
        assert hasattr(ConcreteDatabaseProvider, "friendly_name")
        assert hasattr(ConcreteDatabaseProvider, "description")
        assert hasattr(ConcreteDatabaseProvider, "db_type")
        assert hasattr(ConcreteDatabaseProvider, "extension")
        assert ConcreteDatabaseProvider.extension == EXT_Database

    def test_provider_abilities_structure(self):
        """Test provider abilities structure"""
        abilities = ConcreteDatabaseProvider._abilities
        assert isinstance(abilities, set)
        assert "database" in abilities
        assert "sql" in abilities
        assert "data_storage" in abilities

    def test_get_db_type_method(self):
        """Test database type retrieval method"""
        db_type = ConcreteDatabaseProvider.get_db_type()
        assert db_type == "test"

    def test_provider_info_structure(self):
        """Test provider info structure"""
        info = ConcreteDatabaseProvider.get_provider_info()
        assert isinstance(info, dict)
        assert "name" in info
        assert "friendly_name" in info
        assert "description" in info
        assert "type" in info
        assert "classification" in info
        assert "abilities" in info
