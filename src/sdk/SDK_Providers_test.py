from typing import Any, Dict, List

from sdk.AbstractSDKTest import AbstractSDKTest
from sdk.SDK_Providers import (
    ExtensionInstanceAbilitySDK,
    ProviderExtensionAbilitySDK,
    ProviderExtensionSDK,
    ProviderInstanceSDK,
    ProviderInstanceSettingSDK,
    ProviderInstanceUsageSDK,
    ProviderSDK,
    ProvidersSDK,
    RotationProviderInstanceSDK,
    RotationSDK,
)


class TestProviderSDK(AbstractSDKTest):
    """Tests for the ProviderSDK module using configuration-driven approach."""

    sdk_class = ProviderSDK
    resource_name = "provider"
    sample_data = {
        "name": "test_provider",
        "friendly_name": "Test Provider",
        "agent_settings_json": '{"api_base": "https://api.test.com"}',
    }
    update_data = {"friendly_name": "Updated Provider"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "name": f"test_provider_{resource_type}",
            "friendly_name": f"Test {resource_type} Provider",
            "agent_settings_json": '{"api_base": "https://api.test.com"}',
        }
        return [{**base_data, "name": f"{base_data['name']}_{i}"} for i in range(count)]

    def assert_valid_response_structure(
        self,
        response: Dict[str, Any],
        expected_keys: List[str],
        resource_key: str = None,
    ):
        """Assert that a response has the expected structure."""
        if resource_key:
            assert resource_key in response, f"Response missing '{resource_key}' key"
            data = response[resource_key]
        else:
            data = response

        for key in expected_keys:
            assert key in data, f"Response missing expected key: {key}"

    def test_get_provider_status(self):
        """Test getting provider status."""
        # Create a provider first
        with self.mock_request_context({"id": "provider_123"}) as mock_client:
            provider = self.sdk.create_provider(
                name="status_test_provider",
                friendly_name="Status Test Provider",
            )

        # Test get provider status
        with self.mock_request_context({"status": "active"}) as mock_client:
            response = self.sdk.get_provider_status(provider["id"])
            assert response is not None


class TestProviderInstanceSDK(AbstractSDKTest):
    """Tests for the ProviderInstanceSDK module using configuration-driven approach."""

    sdk_class = ProviderInstanceSDK
    resource_name = "provider_instance"
    sample_data = {
        "name": "test_instance",
        "provider_id": "provider_123",
        "model_name": "gpt-4",
        "api_key": "test_api_key",
    }
    update_data = {"model_name": "gpt-3.5-turbo"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "name": f"test_instance_{resource_type}",
            "provider_id": "provider_123",
            "model_name": "gpt-4",
            "api_key": "test_api_key",
        }
        return [{**base_data, "name": f"{base_data['name']}_{i}"} for i in range(count)]

    def assert_valid_response_structure(
        self,
        response: Dict[str, Any],
        expected_keys: List[str],
        resource_key: str = None,
    ):
        """Assert that a response has the expected structure."""
        if resource_key:
            assert resource_key in response, f"Response missing '{resource_key}' key"
            data = response[resource_key]
        else:
            data = response

        for key in expected_keys:
            assert key in data, f"Response missing expected key: {key}"


class TestProviderInstanceSettingSDK(AbstractSDKTest):
    """Tests for the ProviderInstanceSettingSDK module using configuration-driven approach."""

    sdk_class = ProviderInstanceSettingSDK
    resource_name = "provider_instance_setting"
    sample_data = {
        "provider_instance_id": "instance_123",
        "key": "test_setting",
        "value": "test_value",
    }
    update_data = {"value": "updated_value"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "provider_instance_id": "instance_123",
            "key": f"test_setting_{resource_type}",
            "value": f"test_value_{resource_type}",
        }
        return [{**base_data, "key": f"{base_data['key']}_{i}"} for i in range(count)]

    def assert_valid_response_structure(
        self,
        response: Dict[str, Any],
        expected_keys: List[str],
        resource_key: str = None,
    ):
        """Assert that a response has the expected structure."""
        if resource_key:
            assert resource_key in response, f"Response missing '{resource_key}' key"
            data = response[resource_key]
        else:
            data = response

        for key in expected_keys:
            assert key in data, f"Response missing expected key: {key}"


class TestProviderExtensionSDK(AbstractSDKTest):
    """Tests for the ProviderExtensionSDK module using configuration-driven approach."""

    sdk_class = ProviderExtensionSDK
    resource_name = "provider_extension"
    sample_data = {"provider_id": "provider_123", "extension_id": "extension_123"}
    update_data = {"enabled": True}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {"provider_id": "provider_123", "extension_id": "extension_123"}
        return [base_data for _ in range(count)]

    def assert_valid_response_structure(
        self,
        response: Dict[str, Any],
        expected_keys: List[str],
        resource_key: str = None,
    ):
        """Assert that a response has the expected structure."""
        if resource_key:
            assert resource_key in response, f"Response missing '{resource_key}' key"
            data = response[resource_key]
        else:
            data = response

        for key in expected_keys:
            assert key in data, f"Response missing expected key: {key}"


class TestProviderExtensionAbilitySDK(AbstractSDKTest):
    """Tests for the ProviderExtensionAbilitySDK module using configuration-driven approach."""

    sdk_class = ProviderExtensionAbilitySDK
    resource_name = "provider_extension_ability"
    sample_data = {
        "provider_extension_id": "provider_extension_123",
        "ability_id": "ability_123",
    }
    update_data = {"enabled": True}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "provider_extension_id": "provider_extension_123",
            "ability_id": "ability_123",
        }
        return [base_data for _ in range(count)]

    def assert_valid_response_structure(
        self,
        response: Dict[str, Any],
        expected_keys: List[str],
        resource_key: str = None,
    ):
        """Assert that a response has the expected structure."""
        if resource_key:
            assert resource_key in response, f"Response missing '{resource_key}' key"
            data = response[resource_key]
        else:
            data = response

        for key in expected_keys:
            assert key in data, f"Response missing expected key: {key}"


class TestRotationSDK(AbstractSDKTest):
    """Tests for the RotationSDK module using configuration-driven approach."""

    sdk_class = RotationSDK
    resource_name = "rotation"
    sample_data = {
        "name": "test_rotation",
        "description": "Test rotation description",
    }
    update_data = {"description": "Updated rotation description"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "name": f"test_rotation_{resource_type}",
            "description": f"Test {resource_type} rotation description",
        }
        return [{**base_data, "name": f"{base_data['name']}_{i}"} for i in range(count)]

    def assert_valid_response_structure(
        self,
        response: Dict[str, Any],
        expected_keys: List[str],
        resource_key: str = None,
    ):
        """Assert that a response has the expected structure."""
        if resource_key:
            assert resource_key in response, f"Response missing '{resource_key}' key"
            data = response[resource_key]
        else:
            data = response

        for key in expected_keys:
            assert key in data, f"Response missing expected key: {key}"


class TestRotationProviderInstanceSDK(AbstractSDKTest):
    """Tests for the RotationProviderInstanceSDK module using configuration-driven approach."""

    sdk_class = RotationProviderInstanceSDK
    resource_name = "rotation_provider_instance"
    sample_data = {
        "rotation_id": "rotation_123",
        "provider_instance_id": "instance_123",
    }
    update_data = {"priority": 1}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "rotation_id": "rotation_123",
            "provider_instance_id": "instance_123",
        }
        return [base_data for _ in range(count)]

    def assert_valid_response_structure(
        self,
        response: Dict[str, Any],
        expected_keys: List[str],
        resource_key: str = None,
    ):
        """Assert that a response has the expected structure."""
        if resource_key:
            assert resource_key in response, f"Response missing '{resource_key}' key"
            data = response[resource_key]
        else:
            data = response

        for key in expected_keys:
            assert key in data, f"Response missing expected key: {key}"


class TestProviderInstanceUsageSDK(AbstractSDKTest):
    """Tests for the ProviderInstanceUsageSDK module using configuration-driven approach."""

    sdk_class = ProviderInstanceUsageSDK
    resource_name = "provider_instance_usage"
    sample_data = {
        "provider_instance_id": "instance_123",
        "input_tokens": 100,
        "output_tokens": 50,
        "cost": 0.001,
    }
    update_data = {"cost": 0.002}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "provider_instance_id": "instance_123",
            "input_tokens": 100,
            "output_tokens": 50,
            "cost": 0.001,
        }
        return [base_data for _ in range(count)]

    def assert_valid_response_structure(
        self,
        response: Dict[str, Any],
        expected_keys: List[str],
        resource_key: str = None,
    ):
        """Assert that a response has the expected structure."""
        if resource_key:
            assert resource_key in response, f"Response missing '{resource_key}' key"
            data = response[resource_key]
        else:
            data = response

        for key in expected_keys:
            assert key in data, f"Response missing expected key: {key}"


class TestExtensionInstanceAbilitySDK(AbstractSDKTest):
    """Tests for the ExtensionInstanceAbilitySDK module using configuration-driven approach."""

    sdk_class = ExtensionInstanceAbilitySDK
    resource_name = "extension_instance_ability"
    sample_data = {
        "provider_instance_id": "instance_123",
        "provider_extension_ability_id": "ability_123",
        "state": True,
        "forced": False,
    }
    update_data = {"state": False}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "provider_instance_id": "instance_123",
            "provider_extension_ability_id": "ability_123",
            "state": True,
            "forced": False,
        }
        return [base_data for _ in range(count)]

    def assert_valid_response_structure(
        self,
        response: Dict[str, Any],
        expected_keys: List[str],
        resource_key: str = None,
    ):
        """Assert that a response has the expected structure."""
        if resource_key:
            assert resource_key in response, f"Response missing '{resource_key}' key"
            data = response[resource_key]
        else:
            data = response

        for key in expected_keys:
            assert key in data, f"Response missing expected key: {key}"


class TestProvidersSDK(AbstractSDKTest):
    """Tests for the composite ProvidersSDK module using configuration-driven approach."""

    sdk_class = ProvidersSDK
    resource_name = "providers"
    sample_data = {}
    update_data = {}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        return [{}]

    def assert_valid_response_structure(
        self,
        response: Dict[str, Any],
        expected_keys: List[str],
        resource_key: str = None,
    ):
        """Assert that a response has the expected structure."""
        if resource_key:
            assert resource_key in response, f"Response missing '{resource_key}' key"
            data = response[resource_key]
        else:
            data = response

        for key in expected_keys:
            assert key in data, f"Response missing expected key: {key}"

    def test_providers_sdk_initialization(self):
        """Test that ProvidersSDK initializes all sub-SDKs correctly."""
        # Verify all resource managers are available
        expected_resources = [
            "providers",
            "provider_instances",
            "provider_instance_settings",
            "provider_extensions",
            "provider_extension_abilities",
            "rotations",
            "rotation_provider_instances",
            "provider_instance_usage",
            "extension_instance_abilities",
        ]

        for resource in expected_resources:
            assert hasattr(
                self.sdk, resource
            ), f"ProvidersSDK should have {resource} resource manager"
            assert self.sdk.resource_managers[resource] is not None

    def test_providers_sdk_convenience_methods(self):
        """Test that ProvidersSDK convenience methods work correctly."""
        # Test provider convenience methods
        with self.mock_request_context({"id": "provider_123"}) as mock_client:
            provider_data = {
                "name": "convenience_provider",
                "friendly_name": "Convenience Provider",
            }
            provider = self.sdk.create_provider(**provider_data)
            assert "id" in provider

        # Test provider instance convenience methods
        with self.mock_request_context({"id": "instance_123"}) as mock_client:
            instance_data = {
                "name": "convenience_instance",
                "provider_id": "provider_123",
                "model_name": "gpt-4",
                "team_id": "team_123",
            }
            instance = self.sdk.create_provider_instance(**instance_data)
            assert "id" in instance

        # Test listing methods
        with self.mock_request_context({"items": [], "total": 0}) as mock_client:
            providers = self.sdk.list_providers()
            assert "items" in providers

        with self.mock_request_context({"items": [], "total": 0}) as mock_client:
            instances = self.sdk.list_provider_instances(provider_id="provider_123")
            assert "items" in instances
