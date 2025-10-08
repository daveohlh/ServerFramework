from typing import Any, Dict, List

from sdk.AbstractSDKTest import AbstractSDKTest
from sdk.SDK_Extensions import AbilitySDK, ExtensionSDK, ExtensionsSDK


class TestExtensionSDK(AbstractSDKTest):
    """Tests for the ExtensionSDK module using configuration-driven approach."""

    sdk_class = ExtensionSDK
    resource_name = "extension"
    sample_data = {
        "name": "test_extension",
        "description": "Test extension description",
        "version": "1.0.0",
    }
    update_data = {"description": "Updated extension description"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "name": f"test_extension_{resource_type}",
            "description": f"Test {resource_type} extension description",
            "version": "1.0.0",
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


class TestAbilitySDK(AbstractSDKTest):
    """Tests for the AbilitySDK module using configuration-driven approach."""

    sdk_class = AbilitySDK
    resource_name = "ability"
    sample_data = {
        "name": "test_ability",
        "extension_id": "extension_123",
        "description": "Test ability description",
        "ability_type": "function",
    }
    update_data = {"description": "Updated ability description"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "name": f"test_ability_{resource_type}",
            "extension_id": "extension_123",
            "description": f"Test {resource_type} ability description",
            "ability_type": "function",
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


class TestExtensionsSDK(AbstractSDKTest):
    """Tests for the composite ExtensionsSDK module using configuration-driven approach."""

    sdk_class = ExtensionsSDK
    resource_name = "extensions"
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

    def test_extensions_sdk_initialization(self):
        """Test that ExtensionsSDK initializes all sub-SDKs correctly."""
        # Verify all resource managers are available
        expected_resources = ["extensions", "abilities"]

        for resource in expected_resources:
            assert hasattr(
                self.sdk, resource
            ), f"ExtensionsSDK should have {resource} resource manager"
            assert self.sdk.resource_managers[resource] is not None

    def test_extensions_sdk_convenience_methods(self):
        """Test that ExtensionsSDK convenience methods work correctly."""
        # Test extension convenience methods
        with self.mock_request_context({"id": "extension_123"}) as mock_client:
            extension_data = {
                "name": "convenience_extension",
                "description": "Convenience Extension",
                "version": "1.0.0",
            }
            extension = self.sdk.create_extension(**extension_data)
            assert "id" in extension

        # Test ability convenience methods
        with self.mock_request_context({"id": "ability_123"}) as mock_client:
            ability_data = {
                "name": "convenience_ability",
                "extension_id": "extension_123",
                "description": "Convenience Ability",
                "ability_type": "function",
            }
            ability = self.sdk.create_ability(**ability_data)
            assert "id" in ability

        # Test listing methods
        with self.mock_request_context({"items": [], "total": 0}) as mock_client:
            extensions = self.sdk.list_extensions()
            assert "items" in extensions

        with self.mock_request_context({"items": [], "total": 0}) as mock_client:
            abilities = self.sdk.list_abilities(extension_id="extension_123")
            assert "items" in abilities
