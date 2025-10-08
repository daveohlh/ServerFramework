"""
Tests for PRV_InfluxDB provider.
Tests static provider functionality with Provider Rotation System.
"""

from typing import Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from extensions.database.PRV_InfluxDB import PRV_InfluxDB
from extensions.database.EXT_Database import EXT_Database


class TestPRVInfluxDB:
    """Test suite for PRV_InfluxDB static database provider"""

    def test_provider_metadata(self):
        """Test static provider metadata"""
        assert PRV_InfluxDB.name == "InfluxDB"
        assert PRV_InfluxDB.friendly_name == "InfluxDB Time Series Database"
        assert PRV_InfluxDB.db_type == "influxdb"
        assert PRV_InfluxDB.extension == EXT_Database

    def test_provider_abilities(self):
        """Test provider abilities"""
        abilities = PRV_InfluxDB.get_abilities()

        assert isinstance(abilities, set)
        assert "database" in abilities
        assert "sql" in abilities
        assert "data_storage" in abilities
        assert "time_series" in abilities
        assert "metrics" in abilities
        assert "time_series_db" in abilities

    def test_provider_env_variables(self):
        """Test provider environment variables"""
        env_vars = PRV_InfluxDB._env

        assert isinstance(env_vars, dict)
        assert "INFLUXDB_URL" in env_vars
        assert "INFLUXDB_TOKEN" in env_vars
        assert "INFLUXDB_ORG" in env_vars
        assert "INFLUXDB_BUCKET" in env_vars
        assert "INFLUXDB_VERSION" in env_vars

    def test_get_db_classifications(self):
        """Test database classifications"""
        classifications = PRV_InfluxDB.get_db_classifications()

        assert isinstance(classifications, set)
        assert "time_series" in classifications

    def test_get_provider_info(self):
        """Test provider information"""
        info = PRV_InfluxDB.get_provider_info()

        assert info["name"] == "InfluxDB"
        assert info["type"] == "influxdb"
        assert "time_series" in info["classification"]
        assert isinstance(info["abilities"], list)

    def test_bond_instance_v2(self):
        """Test bonding with InfluxDB 2.x configuration"""
        config = {
            "influxdb_version": "2",
            "influxdb_url": "http://localhost:8086",
            "influxdb_token": "test_token",
            "influxdb_org": "test_org",
            "influxdb_bucket": "test_bucket",
        }

        with patch("extensions.database.PRV_InfluxDB.has_influxdb2", True):
            PRV_InfluxDB.bond_instance(config)

            assert PRV_InfluxDB._connection_config["influxdb_version"] == "2"
            assert (
                PRV_InfluxDB._connection_config["influxdb_url"]
                == "http://localhost:8086"
            )
            assert PRV_InfluxDB._connection_config["influxdb_token"] == "test_token"

    def test_bond_instance_v1(self):
        """Test bonding with InfluxDB 1.x configuration"""
        config = {
            "influxdb_version": "1",
            "database_host": "localhost",
            "database_port": "8086",
            "database_name": "test_db",
            "database_username": "test_user",
            "database_password": "test_pass",
        }

        with patch("extensions.database.PRV_InfluxDB.influxdb", MagicMock()):
            PRV_InfluxDB.bond_instance(config)

            assert PRV_InfluxDB._connection_config["influxdb_version"] == "1"
            assert PRV_InfluxDB._connection_config["database_host"] == "localhost"
            assert PRV_InfluxDB._connection_config["database_name"] == "test_db"

    def test_bond_instance_v2_missing_library(self):
        """Test bonding with InfluxDB 2.x when library is missing"""
        config = {"influxdb_version": "2"}

        with patch("extensions.database.PRV_InfluxDB.has_influxdb2", False):
            with pytest.raises(
                ImportError, match="InfluxDB 2.x client library not installed"
            ):
                PRV_InfluxDB.bond_instance(config)

    def test_bond_instance_v1_missing_library(self):
        """Test bonding with InfluxDB 1.x when library is missing"""
        config = {"influxdb_version": "1"}

        with patch("extensions.database.PRV_InfluxDB.influxdb", None):
            with pytest.raises(
                ImportError, match="InfluxDB 1.x client library not installed"
            ):
                PRV_InfluxDB.bond_instance(config)

    def test_get_connection_v2(self):
        """Test connection retrieval for InfluxDB 2.x"""
        config = {
            "influxdb_version": "2",
            "influxdb_url": "http://localhost:8086",
            "influxdb_token": "test_token",
            "influxdb_org": "test_org",
        }
        PRV_InfluxDB._connection_config = config

        mock_client = MagicMock()
        with patch("extensions.database.PRV_InfluxDB.has_influxdb2", True):
            with patch(
                "extensions.database.PRV_InfluxDB.InfluxDBClient2",
                return_value=mock_client,
            ):
                connection = PRV_InfluxDB._get_connection()

                assert connection == mock_client

    def test_get_connection_v1(self):
        """Test connection retrieval for InfluxDB 1.x"""
        config = {
            "influxdb_version": "1",
            "database_host": "localhost",
            "database_port": 8086,
            "database_username": "test_user",
            "database_password": "test_pass",
            "database_name": "test_db",
        }
        PRV_InfluxDB._connection_config = config

        mock_client = MagicMock()
        with patch("extensions.database.PRV_InfluxDB.influxdb", MagicMock()):
            with patch(
                "extensions.database.PRV_InfluxDB.InfluxDBClient",
                return_value=mock_client,
            ):
                connection = PRV_InfluxDB._get_connection()

                assert connection == mock_client

    def test_get_connection_missing_params_v2(self):
        """Test connection retrieval with missing InfluxDB 2.x parameters"""
        config = {
            "influxdb_version": "2",
            "influxdb_url": "",  # Missing URL
            "influxdb_token": "test_token",
            "influxdb_org": "test_org",
        }
        PRV_InfluxDB._connection_config = config

        with patch("extensions.database.PRV_InfluxDB.has_influxdb2", True):
            connection = PRV_InfluxDB._get_connection()
            assert connection is None

    @pytest.mark.asyncio
    async def test_execute_sql_alias(self):
        """Test execute_sql as alias for execute_query"""
        mock_result = "Query executed successfully"

        with patch.object(
            PRV_InfluxDB, "execute_query", return_value=mock_result
        ) as mock_execute_query:
            result = await PRV_InfluxDB.execute_sql("SELECT * FROM measurement")

            assert result == mock_result
            mock_execute_query.assert_called_once_with("SELECT * FROM measurement")

    @pytest.mark.asyncio
    async def test_execute_query_v2_flux(self):
        """Test query execution with InfluxDB 2.x Flux"""
        config = {"influxdb_version": "2", "influxdb_bucket": "test_bucket"}
        PRV_InfluxDB._connection_config = config

        # Mock client and query API
        mock_client = MagicMock()
        mock_query_api = MagicMock()
        mock_client.query_api.return_value = mock_query_api

        # Mock query result
        mock_record = MagicMock()
        mock_record.values = {
            "field1": "value1",
            "field2": "value2",
            "_time": "2023-01-01",
        }
        mock_table = MagicMock()
        mock_table.records = [mock_record]
        mock_query_api.query.return_value = [mock_table]

        with patch.object(PRV_InfluxDB, "_get_connection", return_value=mock_client):
            result = await PRV_InfluxDB.execute_query(
                'from(bucket:"test_bucket") |> range(start: -1h)'
            )

            assert "field1=value1" in result
            assert "field2=value2" in result
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_v1_influxql(self):
        """Test query execution with InfluxDB 1.x InfluxQL"""
        config = {"influxdb_version": "1"}
        PRV_InfluxDB._connection_config = config

        # Mock client and query result
        mock_client = MagicMock()
        mock_point = {"time": "2023-01-01", "value": 42}
        mock_series = [mock_point]
        mock_client.query.return_value = [mock_series]

        with patch.object(PRV_InfluxDB, "_get_connection", return_value=mock_client):
            result = await PRV_InfluxDB.execute_query("SELECT * FROM measurement")

            assert "time=2023-01-01" in result
            assert "value=42" in result

    @pytest.mark.asyncio
    async def test_execute_query_clean_format(self):
        """Test query execution with various query formats"""
        config = {"influxdb_version": "2", "influxdb_bucket": "test"}
        PRV_InfluxDB._connection_config = config

        mock_client = MagicMock()
        mock_client.query_api.return_value.query.return_value = []

        with patch.object(PRV_InfluxDB, "_get_connection", return_value=mock_client):
            # Test query in code block
            query_with_markdown = """```flux
            from(bucket:"test") |> range(start: -1h)
            ```"""

            result = await PRV_InfluxDB.execute_query(query_with_markdown)
            assert "No data returned" in result

    @pytest.mark.asyncio
    async def test_execute_query_no_connection(self):
        """Test query execution when connection fails"""
        with patch.object(PRV_InfluxDB, "_get_connection", return_value=None):
            result = await PRV_InfluxDB.execute_query("SELECT * FROM test")

            assert "Error connecting to InfluxDB" in result

    @pytest.mark.asyncio
    async def test_execute_query_error_handling(self):
        """Test query execution error handling"""
        mock_client = MagicMock()
        mock_client.query_api.side_effect = Exception("Connection failed")

        with patch.object(PRV_InfluxDB, "_get_connection", return_value=mock_client):
            result = await PRV_InfluxDB.execute_query("INVALID QUERY")

            assert "Error executing query" in result
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_schema_v2(self):
        """Test schema retrieval for InfluxDB 2.x"""
        config = {"influxdb_version": "2", "influxdb_bucket": "test_bucket"}
        PRV_InfluxDB._connection_config = config

        # Mock client and query API
        mock_client = MagicMock()
        mock_query_api = MagicMock()
        mock_client.query_api.return_value = mock_query_api

        # Mock measurement query result
        mock_record = MagicMock()
        mock_record.get_value.return_value = "temperature"
        mock_table = MagicMock()
        mock_table.records = [mock_record]
        mock_query_api.query.return_value = [mock_table]

        with patch.object(PRV_InfluxDB, "_get_connection", return_value=mock_client):
            result = await PRV_InfluxDB.get_schema()

            assert "InfluxDB 2.x Bucket: test_bucket" in result
            assert "Measurements:" in result
            assert "temperature" in result

    @pytest.mark.asyncio
    async def test_get_schema_v1(self):
        """Test schema retrieval for InfluxDB 1.x"""
        config = {"influxdb_version": "1", "database_name": "test_db"}
        PRV_InfluxDB._connection_config = config

        # Mock client and measurements query
        mock_client = MagicMock()
        mock_measurement_point = {"name": "temperature"}
        mock_series = [mock_measurement_point]
        mock_client.query.return_value = [mock_series]

        with patch.object(PRV_InfluxDB, "_get_connection", return_value=mock_client):
            result = await PRV_InfluxDB.get_schema()

            assert "InfluxDB 1.x Database: test_db" in result
            assert "Measurements:" in result
            assert "temperature" in result

    @pytest.mark.asyncio
    async def test_get_schema_no_bucket_v2(self):
        """Test schema retrieval without bucket configured"""
        config = {"influxdb_version": "2", "influxdb_bucket": ""}
        PRV_InfluxDB._connection_config = config

        mock_client = MagicMock()

        with patch.object(PRV_InfluxDB, "_get_connection", return_value=mock_client):
            result = await PRV_InfluxDB.get_schema()

            assert "No bucket configured" in result

    @pytest.mark.asyncio
    async def test_chat_with_db_v2(self):
        """Test database chat for InfluxDB 2.x"""
        config = {"influxdb_version": "2"}
        PRV_InfluxDB._connection_config = config

        with patch.object(PRV_InfluxDB, "get_schema", return_value="Schema info"):
            result = await PRV_InfluxDB.chat_with_db("Show me temperature data")

            assert "natural language query" in result.lower()
            assert "flux" in result.lower()
            assert "from(bucket:" in result

    @pytest.mark.asyncio
    async def test_chat_with_db_v1(self):
        """Test database chat for InfluxDB 1.x"""
        config = {"influxdb_version": "1"}
        PRV_InfluxDB._connection_config = config

        with patch.object(PRV_InfluxDB, "get_schema", return_value="Schema info"):
            result = await PRV_InfluxDB.chat_with_db("Show me temperature data")

            assert "natural language query" in result.lower()
            assert "influxql" in result.lower()
            assert "SELECT" in result

    @pytest.mark.asyncio
    async def test_write_data_v2(self):
        """Test data writing for InfluxDB 2.x"""
        config = {
            "influxdb_version": "2",
            "influxdb_bucket": "test_bucket",
            "influxdb_org": "test_org",
        }
        PRV_InfluxDB._connection_config = config

        mock_client = MagicMock()
        mock_write_api = MagicMock()
        mock_client.write_api.return_value = mock_write_api

        with patch.object(PRV_InfluxDB, "_get_connection", return_value=mock_client):
            with patch("extensions.database.PRV_InfluxDB.SYNCHRONOUS", "sync_mode"):
                result = await PRV_InfluxDB.write_data(
                    "temperature,sensor=1 value=23.5"
                )

                assert "Data written successfully to InfluxDB 2.x" in result
                mock_write_api.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_data_v1_json(self):
        """Test data writing for InfluxDB 1.x with JSON data"""
        config = {"influxdb_version": "1"}
        PRV_InfluxDB._connection_config = config

        mock_client = MagicMock()

        with patch.object(PRV_InfluxDB, "_get_connection", return_value=mock_client):
            json_data = '[{"measurement": "temperature", "fields": {"value": 23.5}}]'
            result = await PRV_InfluxDB.write_data(json_data)

            assert "Data written successfully to InfluxDB 1.x" in result
            mock_client.write_points.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_data_missing_config_v2(self):
        """Test data writing with missing configuration for InfluxDB 2.x"""
        config = {
            "influxdb_version": "2",
            "influxdb_bucket": "",  # Missing bucket
            "influxdb_org": "test_org",
        }
        PRV_InfluxDB._connection_config = config

        mock_client = MagicMock()

        with patch.object(PRV_InfluxDB, "_get_connection", return_value=mock_client):
            result = await PRV_InfluxDB.write_data("test data")

            assert "Bucket or organization not configured" in result

    def test_validate_config_v2_complete(self):
        """Test configuration validation for complete InfluxDB 2.x setup"""
        config = {
            "influxdb_version": "2",
            "influxdb_url": "http://localhost:8086",
            "influxdb_token": "test_token",
            "influxdb_org": "test_org",
            "influxdb_bucket": "test_bucket",
        }
        PRV_InfluxDB._connection_config = config

        with patch("extensions.database.PRV_InfluxDB.has_influxdb2", True):
            with patch.object(
                PRV_InfluxDB, "_get_connection", return_value=MagicMock()
            ):
                issues = PRV_InfluxDB.validate_config()

                assert len(issues) == 0

    def test_validate_config_v2_missing_fields(self):
        """Test configuration validation for incomplete InfluxDB 2.x setup"""
        config = {
            "influxdb_version": "2",
            "influxdb_url": "",  # Missing
            "influxdb_token": "test_token",
            "influxdb_org": "",  # Missing
            "influxdb_bucket": "test_bucket",
        }
        PRV_InfluxDB._connection_config = config

        with patch("extensions.database.PRV_InfluxDB.has_influxdb2", True):
            issues = PRV_InfluxDB.validate_config()

            assert len(issues) >= 2
            issue_text = " ".join(issues).lower()
            assert "influxdb url not configured" in issue_text
            assert "influxdb org not configured" in issue_text

    def test_validate_config_v1_complete(self):
        """Test configuration validation for complete InfluxDB 1.x setup"""
        config = {
            "influxdb_version": "1",
            "database_host": "localhost",
            "database_name": "test_db",
            "database_username": "test_user",
            "database_password": "test_pass",
        }
        PRV_InfluxDB._connection_config = config

        with patch("extensions.database.PRV_InfluxDB.influxdb", MagicMock()):
            with patch.object(
                PRV_InfluxDB, "_get_connection", return_value=MagicMock()
            ):
                issues = PRV_InfluxDB.validate_config()

                assert len(issues) == 0

    def test_validate_config_v1_missing_fields(self):
        """Test configuration validation for incomplete InfluxDB 1.x setup"""
        config = {
            "influxdb_version": "1",
            "database_host": "",  # Missing
            "database_name": "test_db",
            "database_username": "",  # Missing
            "database_password": "test_pass",
        }
        PRV_InfluxDB._connection_config = config

        with patch("extensions.database.PRV_InfluxDB.influxdb", MagicMock()):
            issues = PRV_InfluxDB.validate_config()

            assert len(issues) >= 2
            issue_text = " ".join(issues).lower()
            assert "database host not configured" in issue_text
            assert "database username not configured" in issue_text

    def test_validate_config_missing_libraries(self):
        """Test configuration validation with missing client libraries"""
        config = {"influxdb_version": "2"}
        PRV_InfluxDB._connection_config = config

        with patch("extensions.database.PRV_InfluxDB.has_influxdb2", False):
            issues = PRV_InfluxDB.validate_config()

            assert len(issues) > 0
            assert any("2.x client library not installed" in issue for issue in issues)

    def test_validate_config_connection_failure(self):
        """Test configuration validation with connection failure"""
        config = {
            "influxdb_version": "2",
            "influxdb_url": "http://localhost:8086",
            "influxdb_token": "test_token",
            "influxdb_org": "test_org",
            "influxdb_bucket": "test_bucket",
        }
        PRV_InfluxDB._connection_config = config

        with patch("extensions.database.PRV_InfluxDB.has_influxdb2", True):
            with patch.object(PRV_InfluxDB, "_get_connection", return_value=None):
                issues = PRV_InfluxDB.validate_config()

                assert len(issues) > 0
                assert any("cannot establish" in issue.lower() for issue in issues)
