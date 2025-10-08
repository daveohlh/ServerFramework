"""
Abstract SDK Test module providing base functionality for testing SDK modules.

This module contains base test classes and utilities for testing SDK functionality,
including mocking HTTP requests and responses, standardized test patterns,
configuration-driven test generation, and resource management.

This follows patterns similar to AbstractEPTest to provide comprehensive
test coverage with minimal code duplication.
"""

import unittest
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Type
from unittest.mock import Mock, patch

from sdk.AbstractSDKHandler import AbstractSDKHandler, ResourceConfig, SDKException


class TestVariant(str, Enum):
    """Variants of test data for testing."""

    VALID = "valid"
    MINIMAL = "minimal"
    INVALID = "invalid"
    EMPTY = "empty"
    LARGE = "large"


class TestOperation(str, Enum):
    """SDK operations that can be tested."""

    CREATE = "create"
    GET = "get"
    LIST = "list"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    BATCH_CREATE = "batch_create"
    BATCH_UPDATE = "batch_update"
    BATCH_DELETE = "batch_delete"


@dataclass
class SDKTestConfig:
    """Configuration for SDK tests."""

    # Operations to test
    test_create: bool = True
    test_get: bool = True
    test_list: bool = True
    test_update: bool = True
    test_delete: bool = True
    test_search: bool = True
    test_batch: bool = True
    test_error_handling: bool = True
    test_authentication: bool = True

    # Test data configuration
    create_data_variants: List[TestVariant] = None
    update_data_variants: List[TestVariant] = None

    # Resource-specific configuration
    primary_resource: str = None  # Primary resource to test
    test_resources: List[str] = None  # List of resources to test

    def __post_init__(self):
        if self.create_data_variants is None:
            self.create_data_variants = [TestVariant.VALID, TestVariant.MINIMAL]
        if self.update_data_variants is None:
            self.update_data_variants = [TestVariant.VALID]
        if self.test_resources is None:
            self.test_resources = []


class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    @property
    def is_success(self):
        return 200 <= self.status_code < 300


class AbstractSDKTest(unittest.TestCase, ABC):
    """Base test class for SDK modules.

    This class provides common testing utilities and patterns for testing
    SDK functionality, including mocking HTTP requests and responses.
    It follows a configuration-driven approach similar to AbstractEPTest
    to provide comprehensive test coverage with minimal code duplication.

    Child classes must override:
    - sdk_class: The SDK class being tested
    - resource_name: The primary resource name being tested
    - sample_data: Sample data for creating test entities
    - update_data: Sample data for updating test entities

    Optional overrides:
    - test_config: Test configuration to customize which tests run
    - resource_configs: Expected resource configurations for the SDK
    """

    # Required overrides that child classes must provide
    sdk_class: Type[AbstractSDKHandler] = None
    resource_name: str = None
    sample_data: Dict[str, Any] = None
    update_data: Dict[str, Any] = None

    # Optional overrides
    test_config: SDKTestConfig = SDKTestConfig()
    resource_configs: Dict[str, ResourceConfig] = None

    # Base URL for testing
    base_url: str = "https://api.test.com"
    test_token: str = "test_token_123"
    test_api_key: str = "test_api_key_456"

    def setUp(self):
        """Set up test fixtures."""
        # Validate required overrides
        assert (
            self.sdk_class is not None
        ), f"{self.__class__.__name__}: sdk_class must be defined"
        assert (
            self.resource_name is not None
        ), f"{self.__class__.__name__}: resource_name must be defined"
        assert (
            self.sample_data is not None
        ), f"{self.__class__.__name__}: sample_data must be defined"
        assert (
            self.update_data is not None
        ), f"{self.__class__.__name__}: update_data must be defined"

        # Create SDK handler instance for testing
        self.sdk = self.sdk_class(
            base_url=self.base_url, token=self.test_token, timeout=30, verify_ssl=False
        )

        # Mock HTTP client
        self.mock_client = Mock()
        self.mock_response = MockResponse({"test": "data"})

        # Track created entities for cleanup
        self.created_entities = []

    def tearDown(self):
        """Clean up after tests."""
        # Clean up any created entities
        self.created_entities.clear()

    def create_mock_response(
        self, data: Dict[str, Any], status_code: int = 200
    ) -> MockResponse:
        """Create a mock HTTP response.

        Args:
            data: Response data
            status_code: HTTP status code

        Returns:
            MockResponse instance
        """
        return MockResponse(data, status_code)

    def create_error_response(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ) -> MockResponse:
        """Create a mock error response.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details

        Returns:
            MockResponse instance with error data
        """
        error_data = {"detail": message}
        if details:
            error_data.update(details)
        return MockResponse(error_data, status_code)

    def get_test_data(self, variant: TestVariant = TestVariant.VALID) -> Dict[str, Any]:
        """Get test data for the specified variant.

        Args:
            variant: The test data variant to return

        Returns:
            Test data dictionary
        """
        if variant == TestVariant.VALID:
            return self.sample_data.copy()
        elif variant == TestVariant.MINIMAL:
            return self._get_minimal_data()
        elif variant == TestVariant.INVALID:
            return self._get_invalid_data()
        elif variant == TestVariant.EMPTY:
            return {}
        elif variant == TestVariant.LARGE:
            return self._get_large_data()
        else:
            return self.sample_data.copy()

    def _get_minimal_data(self) -> Dict[str, Any]:
        """Get minimal test data with only required fields."""
        # Default implementation - subclasses should override
        return {k: v for k, v in self.sample_data.items() if k in ["name", "id"]}

    def _get_invalid_data(self) -> Dict[str, Any]:
        """Get invalid test data for validation testing."""
        # Default implementation - subclasses should override
        invalid_data = self.sample_data.copy()
        # Make some fields invalid
        if "name" in invalid_data:
            invalid_data["name"] = 123  # Invalid type
        if "email" in invalid_data:
            invalid_data["email"] = "invalid-email"  # Invalid format
        return invalid_data

    def _get_large_data(self) -> Dict[str, Any]:
        """Get large test data for stress testing."""
        # Default implementation - subclasses should override
        large_data = self.sample_data.copy()
        if "description" in large_data:
            large_data["description"] = "x" * 10000  # Very long description
        return large_data

    def mock_request(
        self,
        mock_client_class: Mock,
        response_data: Dict[str, Any],
        status_code: int = 200,
    ):
        """Context manager for mocking HTTP requests.

        Args:
            mock_client_class: Mock client class
            response_data: Data to return in response
            status_code: HTTP status code to return
        """
        mock_client = Mock()
        mock_response = MockResponse(response_data, status_code)
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        return mock_client

    @contextmanager
    def mock_request_context(
        self,
        response_data: Dict[str, Any],
        status_code: int = 200,
    ):
        """Context manager for mocking HTTP requests with automatic cleanup.

        Args:
            response_data: Data to return in response
            status_code: HTTP status code to return
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_response = MockResponse(response_data, status_code)
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            yield mock_client

    def assert_request_called_with(
        self,
        mock_client: Mock,
        method: str,
        expected_url: str,
        expected_data: Optional[Dict[str, Any]] = None,
        expected_headers: Optional[Dict[str, str]] = None,
    ):
        """Assert that a request was called with expected parameters.

        Args:
            mock_client: Mock client instance
            method: Expected HTTP method
            expected_url: Expected URL
            expected_data: Expected request data
            expected_headers: Expected headers
        """
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args

        # Check method and URL
        assert (
            call_args[0][0] == method
        ), f"Expected method {method}, got {call_args[0][0]}"
        assert (
            expected_url in call_args[0][1]
        ), f"Expected URL to contain {expected_url}, got {call_args[0][1]}"

        # Check data if provided
        if expected_data:
            call_kwargs = call_args[1]
            if "json" in call_kwargs:
                assert (
                    call_kwargs["json"] == expected_data
                ), f"Expected data {expected_data}, got {call_kwargs['json']}"

        # Check headers if provided
        if expected_headers:
            call_kwargs = call_args[1]
            if "headers" in call_kwargs:
                for key, value in expected_headers.items():
                    assert (
                        key in call_kwargs["headers"]
                    ), f"Expected header {key} not found"
                    assert (
                        call_kwargs["headers"][key] == value
                    ), f"Expected header {key}={value}, got {call_kwargs['headers'][key]}"

    # Configuration-driven test methods

    def test_sdk_initialization(self):
        """Test SDK initialization with various parameters."""
        # Test with token
        sdk_with_token = self.sdk_class(base_url=self.base_url, token=self.test_token)
        assert sdk_with_token.token == self.test_token
        assert sdk_with_token.base_url == self.base_url

        # Test with API key
        sdk_with_api_key = self.sdk_class(
            base_url=self.base_url, api_key=self.test_api_key
        )
        assert sdk_with_api_key.api_key == self.test_api_key

        # Test with both
        sdk_with_both = self.sdk_class(
            base_url=self.base_url, token=self.test_token, api_key=self.test_api_key
        )
        assert sdk_with_both.token == self.test_token
        assert sdk_with_both.api_key == self.test_api_key

    def test_resource_configuration(self):
        """Test that resources are properly configured."""
        # Check that _configure_resources returns expected structure
        configs = self.sdk._configure_resources()
        assert isinstance(configs, dict), "Resource configs should be a dictionary"

        # If resource_configs is provided, validate against it
        if self.resource_configs:
            for resource_name, expected_config in self.resource_configs.items():
                assert (
                    resource_name in configs
                ), f"Expected resource '{resource_name}' not found in configs"
                actual_config = configs[resource_name]
                assert (
                    actual_config.name == expected_config.name
                ), f"Resource name mismatch for {resource_name}"
                assert (
                    actual_config.endpoint == expected_config.endpoint
                ), f"Endpoint mismatch for {resource_name}"

    def test_resource_managers_created(self):
        """Test that resource managers are properly created."""
        configs = self.sdk._configure_resources()

        for resource_name in configs.keys():
            assert hasattr(
                self.sdk, resource_name
            ), f"Resource manager '{resource_name}' not created as attribute"

            manager = getattr(self.sdk, resource_name)
            assert hasattr(
                manager, "create"
            ), f"Manager {resource_name} missing create method"
            assert hasattr(
                manager, "get"
            ), f"Manager {resource_name} missing get method"
            assert hasattr(
                manager, "list"
            ), f"Manager {resource_name} missing list method"
            assert hasattr(
                manager, "update"
            ), f"Manager {resource_name} missing update method"
            assert hasattr(
                manager, "delete"
            ), f"Manager {resource_name} missing delete method"

    def test_headers_with_token(self):
        """Test header generation with JWT token."""
        headers = self.sdk._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {self.test_token}"

    def test_headers_with_api_key(self):
        """Test header generation with API key."""
        sdk_with_api_key = self.sdk_class(
            base_url=self.base_url, api_key=self.test_api_key
        )
        headers = sdk_with_api_key._get_headers()
        assert "X-API-Key" in headers
        assert headers["X-API-Key"] == self.test_api_key

    def test_url_building(self):
        """Test URL building functionality."""
        # Test basic endpoint
        url = self.sdk._build_url("/v1/test")
        assert url == f"{self.base_url}/v1/test"

        # Test with query parameters
        url = self.sdk._build_url("/v1/test", {"param1": "value1", "param2": "value2"})
        assert "param1=value1" in url
        assert "param2=value2" in url

        # Test with None values (should be filtered out)
        url = self.sdk._build_url("/v1/test", {"param1": "value1", "param2": None})
        assert "param1=value1" in url
        assert "param2" not in url

    def test_successful_request(self):
        """Test successful HTTP request."""
        response_data = {"success": True, "data": "test"}

        with self.mock_request_context(response_data) as mock_client:
            result = self.sdk.get("/v1/test")
            assert result == response_data
            self.assert_request_called_with(mock_client, "GET", "/v1/test")

    def test_post_request_with_data(self):
        """Test POST request with data."""
        request_data = {"name": "test"}
        response_data = {"id": "123", "name": "test"}

        with self.mock_request_context(response_data, 201) as mock_client:
            result = self.sdk.post("/v1/test", data=request_data)
            assert result == response_data
            self.assert_request_called_with(
                mock_client, "POST", "/v1/test", expected_data=request_data
            )

    def test_error_handling(self):
        """Test error handling for various HTTP status codes."""
        # Test 404 error
        with self.mock_request_context({"detail": "Not found"}, 404) as mock_client:
            with self.assertRaises(SDKException):
                self.sdk.get("/v1/test/nonexistent")

    def test_resource_manager_creation(self):
        """Test resource manager creation."""
        if not self.resource_configs:
            # Skip if no resource configs provided
            return

        for resource_name, config in self.resource_configs.items():
            manager = self.sdk.create_resource_manager(config)
            assert manager is not None
            assert manager.config == config
            assert manager.handler == self.sdk

    # Standard CRUD operation tests (configuration-driven)

    def _test_resource_operation(
        self, operation: TestOperation, resource_name: str = None
    ):
        """Test a specific resource operation.

        Args:
            operation: The operation to test
            resource_name: Resource to test (defaults to primary resource)
        """
        if not self.test_config.primary_resource and not resource_name:
            resource_name = self.resource_name
        else:
            resource_name = resource_name or self.test_config.primary_resource

        if not hasattr(self.sdk, resource_name):
            self.skipTest(f"Resource manager '{resource_name}' not available")

        manager = getattr(self.sdk, resource_name)

        # Test based on operation type
        if operation == TestOperation.CREATE:
            self._test_create_operation(manager)
        elif operation == TestOperation.GET:
            self._test_get_operation(manager)
        elif operation == TestOperation.LIST:
            self._test_list_operation(manager)
        elif operation == TestOperation.UPDATE:
            self._test_update_operation(manager)
        elif operation == TestOperation.DELETE:
            self._test_delete_operation(manager)
        elif operation == TestOperation.SEARCH:
            self._test_search_operation(manager)
        elif operation == TestOperation.BATCH_CREATE:
            self._test_batch_create_operation(manager)
        elif operation == TestOperation.BATCH_UPDATE:
            self._test_batch_update_operation(manager)
        elif operation == TestOperation.BATCH_DELETE:
            self._test_batch_delete_operation(manager)

    def _test_create_operation(self, manager):
        """Test create operation for a resource manager."""
        response_data = {manager.config.name: {"id": "123", **self.sample_data}}

        with self.mock_request_context(response_data, 201) as mock_client:
            result = manager.create(self.sample_data)
            assert result == response_data

    def _test_get_operation(self, manager):
        """Test get operation for a resource manager."""
        response_data = {manager.config.name: {"id": "123", **self.sample_data}}

        with self.mock_request_context(response_data) as mock_client:
            result = manager.get("123")
            assert result == response_data

    def _test_list_operation(self, manager):
        """Test list operation for a resource manager."""
        response_data = {
            manager.config.name_plural: [{"id": "123", **self.sample_data}],
            "total": 1,
            "offset": 0,
            "limit": 100,
        }

        with self.mock_request_context(response_data) as mock_client:
            result = manager.list()
            assert result == response_data

    def _test_update_operation(self, manager):
        """Test update operation for a resource manager."""
        response_data = {manager.config.name: {"id": "123", **self.update_data}}

        with self.mock_request_context(response_data) as mock_client:
            result = manager.update("123", self.update_data)
            assert result == response_data

    def _test_delete_operation(self, manager):
        """Test delete operation for a resource manager."""
        with self.mock_request_context({}, 204) as mock_client:
            manager.delete("123")  # Should not raise an exception

    def _test_search_operation(self, manager):
        """Test search operation for a resource manager."""
        if not manager.config.supports_search:
            with self.assertRaises(SDKException):
                manager.search({"name": "test"})
            return

        response_data = {
            manager.config.name_plural: [{"id": "123", **self.sample_data}],
            "total": 1,
            "offset": 0,
            "limit": 100,
        }

        with self.mock_request_context(response_data) as mock_client:
            result = manager.search({"name": "test"})
            assert result == response_data

    def _test_batch_create_operation(self, manager):
        """Test batch create operation for a resource manager."""
        if not manager.config.supports_batch:
            with self.assertRaises(SDKException):
                manager.batch_create([self.sample_data])
            return

        response_data = {
            manager.config.name_plural: [{"id": "123", **self.sample_data}]
        }

        with self.mock_request_context(response_data, 201) as mock_client:
            result = manager.batch_create([self.sample_data])
            assert result == response_data

    def _test_batch_update_operation(self, manager):
        """Test batch update operation for a resource manager."""
        if not manager.config.supports_batch:
            with self.assertRaises(SDKException):
                manager.batch_update(self.update_data, ["123"])
            return

        response_data = {
            manager.config.name_plural: [{"id": "123", **self.update_data}]
        }

        with self.mock_request_context(response_data) as mock_client:
            result = manager.batch_update(self.update_data, ["123"])
            assert result == response_data

    def _test_batch_delete_operation(self, manager):
        """Test batch delete operation for a resource manager."""
        if not manager.config.supports_batch:
            with self.assertRaises(SDKException):
                manager.batch_delete(["123"])
            return

        with self.mock_request_context({}, 204) as mock_client:
            manager.batch_delete(["123"])  # Should not raise an exception

    # Abstract methods for subclasses to implement
    @abstractmethod
    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type.

        Args:
            resource_type: Type of resource to create data for
            count: Number of test data items to create

        Returns:
            List of test data dictionaries
        """
        pass

    @abstractmethod
    def assert_valid_response_structure(
        self,
        response: Dict[str, Any],
        expected_keys: List[str],
        resource_key: Optional[str] = None,
    ):
        """Assert that a response has the expected structure.

        Args:
            response: Response data to validate
            expected_keys: Keys that should be present in the response
            resource_key: Key containing the main resource data
        """
        pass

    def assert_pagination_response(self, response: Dict[str, Any], resource_key: str):
        """Assert that a response contains proper pagination information.

        Args:
            response: Response data to validate
            resource_key: Key containing the resource list
        """
        assert resource_key in response, f"Response missing '{resource_key}' key"
        assert isinstance(
            response[resource_key], list
        ), f"'{resource_key}' should be a list"

        # Check for pagination metadata
        pagination_keys = ["total", "offset", "limit"]
        for key in pagination_keys:
            if key in response:
                assert isinstance(
                    response[key], int
                ), f"Pagination key '{key}' should be an integer"


def create_test_suite(test_class) -> unittest.TestSuite:
    """Create a test suite for the given test class.

    Args:
        test_class: Test class to create suite for

    Returns:
        Test suite containing all tests from the class
    """
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(test_class)


def run_test_suite(test_class, verbosity: int = 2) -> unittest.TestResult:
    """Run tests for the given test class.

    Args:
        test_class: Test class to run
        verbosity: Test output verbosity level

    Returns:
        Test results
    """
    suite = create_test_suite(test_class)
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)
