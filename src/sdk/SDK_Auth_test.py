from typing import Any, Dict, List

from sdk.AbstractSDKTest import AbstractSDKTest
from sdk.SDK_Auth import (
    ApiKeySDK,
    AuthSDK,
    FailedLoginSDK,
    InvitationSDK,
    NotificationSDK,
    PermissionSDK,
    RecoveryQuestionSDK,
    RoleSDK,
    SessionSDK,
    TeamMetadataSDK,
    TeamSDK,
    UserCredentialSDK,
    UserMetadataSDK,
    UserSDK,
    UserTeamSDK,
)


class TestUserSDK(AbstractSDKTest):
    """Tests for the UserSDK module using configuration-driven approach."""

    sdk_class = UserSDK
    resource_name = "user"
    sample_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password",
        "first_name": "Test",
        "last_name": "User",
    }
    update_data = {"email": "updated@example.com"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "username": f"test_user_{resource_type}",
            "email": f"test_{resource_type}@example.com",
            "password": "test_password",
            "first_name": "Test",
            "last_name": "User",
        }
        return [
            {
                **base_data,
                "username": f"{base_data['username']}_{i}",
                "email": f"test_{resource_type}_{i}@example.com",
            }
            for i in range(count)
        ]

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

    def test_login(self):
        """Test user login functionality."""
        # Test login with valid credentials
        with self.mock_request_context({"token": "test_token"}) as mock_client:
            response = self.sdk.login("admin", "admin")
            assert "token" in response
            assert response["token"] == "test_token"

    def test_logout(self):
        """Test user logout functionality."""
        with self.mock_request_context({}) as mock_client:
            self.sdk.logout()
            # Verify token is cleared
            assert self.sdk.token is None

    def test_verify_token(self):
        """Test token verification."""
        with self.mock_request_context({"valid": True}) as mock_client:
            result = self.sdk.verify_token()
            assert result is True

    def test_register(self):
        """Test user registration."""
        with self.mock_request_context({"id": "user_123"}) as mock_client:
            response = self.sdk.register(
                email="new@example.com",
                password="new_password",
                first_name="New",
                last_name="User",
            )
            assert "id" in response

    def test_change_password(self):
        """Test password change functionality."""
        with self.mock_request_context({"success": True}) as mock_client:
            response = self.sdk.change_password("old_password", "new_password")
            assert response is not None

    def test_get_current_user(self):
        """Test getting current user."""
        with self.mock_request_context(
            {"id": "user_123", "email": "test@example.com"}
        ) as mock_client:
            response = self.sdk.get_current_user()
            assert "id" in response

    def test_update_current_user(self):
        """Test updating current user."""
        with self.mock_request_context(
            {"id": "user_123", "email": "updated@example.com"}
        ) as mock_client:
            response = self.sdk.update_current_user(email="updated@example.com")
            assert response is not None


class TestTeamSDK(AbstractSDKTest):
    """Tests for the TeamSDK module using configuration-driven approach."""

    sdk_class = TeamSDK
    resource_name = "team"
    sample_data = {"name": "test_team", "description": "Test team description"}
    update_data = {"description": "Updated description"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "name": f"test_team_{resource_type}",
            "description": f"Test {resource_type} description",
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

    def test_get_team_users(self):
        """Test getting team users."""
        with self.mock_request_context({"items": [], "total": 0}) as mock_client:
            response = self.sdk.get_team_users("team_123")
            assert "items" in response


class TestRoleSDK(AbstractSDKTest):
    """Tests for the RoleSDK module using configuration-driven approach."""

    sdk_class = RoleSDK
    resource_name = "role"
    sample_data = {
        "name": "test_role",
        "team_id": "team_123",
        "description": "Test role",
    }
    update_data = {"description": "Updated role description"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "name": f"test_role_{resource_type}",
            "team_id": "team_123",
            "description": f"Test {resource_type}",
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

    def test_list_team_roles(self):
        """Test listing roles for a specific team."""
        with self.mock_request_context({"items": [], "total": 0}) as mock_client:
            response = self.sdk.list_team_roles("team_123")
            assert "items" in response


class TestUserTeamSDK(AbstractSDKTest):
    """Tests for the UserTeamSDK module using configuration-driven approach."""

    sdk_class = UserTeamSDK
    resource_name = "user_team"
    sample_data = {"user_id": "user_123", "team_id": "team_123", "role_id": "role_123"}
    update_data = {"role_id": "role_456"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "user_id": "user_123",
            "team_id": "team_123",
            "role_id": "role_123",
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


class TestInvitationSDK(AbstractSDKTest):
    """Tests for the InvitationSDK module using configuration-driven approach."""

    sdk_class = InvitationSDK
    resource_name = "invitation"
    sample_data = {
        "email": "invite@example.com",
        "team_id": "team_123",
        "role_id": "role_123",
    }
    update_data = {"role_id": "role_456"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "email": f"invite_{resource_type}@example.com",
            "team_id": "team_123",
            "role_id": "role_123",
        }
        return [
            {**base_data, "email": f"invite_{resource_type}_{i}@example.com"}
            for i in range(count)
        ]

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

    def test_accept_invitation(self):
        """Test accepting an invitation."""
        with self.mock_request_context({"success": True}) as mock_client:
            response = self.sdk.accept_invitation("invitation_123")
            assert response is not None


class TestSessionSDK(AbstractSDKTest):
    """Tests for the SessionSDK module using configuration-driven approach."""

    sdk_class = SessionSDK
    resource_name = "session"
    sample_data = {"user_id": "user_123"}
    update_data = {}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {"user_id": "user_123"}
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

    def test_get_sessions(self):
        """Test getting sessions."""
        with self.mock_request_context({"items": [], "total": 0}) as mock_client:
            response = self.sdk.get_sessions()
            assert "items" in response

    def test_list_user_sessions(self):
        """Test listing user sessions."""
        with self.mock_request_context({"items": [], "total": 0}) as mock_client:
            response = self.sdk.list_user_sessions("user_123")
            assert "items" in response


class TestNotificationSDK(AbstractSDKTest):
    """Tests for the NotificationSDK module using configuration-driven approach."""

    sdk_class = NotificationSDK
    resource_name = "notification"
    sample_data = {"user_id": "user_123", "message": "Test notification"}
    update_data = {}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "user_id": "user_123",
            "message": f"Test {resource_type} notification",
        }
        return [
            {**base_data, "message": f"{base_data['message']} {i}"}
            for i in range(count)
        ]

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

    def test_get_notifications(self):
        """Test getting notifications."""
        with self.mock_request_context({"items": [], "total": 0}) as mock_client:
            response = self.sdk.get_notifications()
            assert "items" in response


class TestApiKeySDK(AbstractSDKTest):
    """Tests for the ApiKeySDK module using configuration-driven approach."""

    sdk_class = ApiKeySDK
    resource_name = "api_key"
    sample_data = {"name": "test_api_key", "description": "Test API key"}
    update_data = {"description": "Updated API key description"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "name": f"test_api_key_{resource_type}",
            "description": f"Test {resource_type} API key",
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


class TestUserMetadataSDK(AbstractSDKTest):
    """Tests for the UserMetadataSDK module using configuration-driven approach."""

    sdk_class = UserMetadataSDK
    resource_name = "user_metadata"
    sample_data = {"user_id": "user_123", "key": "test_key", "value": "test_value"}
    update_data = {"value": "updated_value"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "user_id": "user_123",
            "key": f"test_key_{resource_type}",
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


class TestTeamMetadataSDK(AbstractSDKTest):
    """Tests for the TeamMetadataSDK module using configuration-driven approach."""

    sdk_class = TeamMetadataSDK
    resource_name = "team_metadata"
    sample_data = {"team_id": "team_123", "key": "test_key", "value": "test_value"}
    update_data = {"value": "updated_value"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "team_id": "team_123",
            "key": f"test_key_{resource_type}",
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


class TestUserCredentialSDK(AbstractSDKTest):
    """Tests for the UserCredentialSDK module using configuration-driven approach."""

    sdk_class = UserCredentialSDK
    resource_name = "user_credential"
    sample_data = {
        "user_id": "user_123",
        "credential_type": "password",
        "credential_data": "test_credential",
    }
    update_data = {"credential_data": "updated_credential"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "user_id": "user_123",
            "credential_type": "password",
            "credential_data": f"test_credential_{resource_type}",
        }
        return [
            {**base_data, "credential_data": f"{base_data['credential_data']}_{i}"}
            for i in range(count)
        ]

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


class TestRecoveryQuestionSDK(AbstractSDKTest):
    """Tests for the RecoveryQuestionSDK module using configuration-driven approach."""

    sdk_class = RecoveryQuestionSDK
    resource_name = "recovery_question"
    sample_data = {
        "user_id": "user_123",
        "question": "What is your favorite color?",
        "answer_hash": "blue_hash",
    }
    update_data = {"answer_hash": "red_hash"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "user_id": "user_123",
            "question": f"What is your favorite {resource_type}?",
            "answer_hash": f"{resource_type}_hash",
        }
        return [
            {**base_data, "question": f"{base_data['question']}_{i}"}
            for i in range(count)
        ]

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


class TestFailedLoginSDK(AbstractSDKTest):
    """Tests for the FailedLoginSDK module using configuration-driven approach."""

    sdk_class = FailedLoginSDK
    resource_name = "failed_login"
    sample_data = {"user_id": "user_123", "ip_address": "192.168.1.1"}
    update_data = {}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {"user_id": "user_123", "ip_address": "192.168.1.1"}
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


class TestPermissionSDK(AbstractSDKTest):
    """Tests for the PermissionSDK module using configuration-driven approach."""

    sdk_class = PermissionSDK
    resource_name = "permission"
    sample_data = {"name": "test_permission", "description": "Test permission"}
    update_data = {"description": "Updated permission description"}

    def create_test_data(
        self, resource_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Create test data for the specified resource type."""
        base_data = {
            "name": f"test_permission_{resource_type}",
            "description": f"Test {resource_type} permission",
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


class TestAuthSDK(AbstractSDKTest):
    """Tests for the composite AuthSDK module using configuration-driven approach."""

    sdk_class = AuthSDK
    resource_name = "auth"
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

    def test_auth_sdk_initialization(self):
        """Test that AuthSDK initializes all sub-SDKs correctly."""
        # Verify all resource managers are available
        expected_resources = [
            "users",
            "teams",
            "roles",
            "user_teams",
            "invitations",
            "sessions",
            "notifications",
            "api_keys",
            "user_metadata",
            "team_metadata",
            "user_credentials",
            "recovery_questions",
            "failed_logins",
            "permissions",
        ]

        for resource in expected_resources:
            assert hasattr(
                self.sdk, resource
            ), f"AuthSDK should have {resource} resource manager"
            assert self.sdk.resource_managers[resource] is not None

    def test_auth_sdk_convenience_methods(self):
        """Test that AuthSDK convenience methods work correctly."""
        # Test user convenience methods
        with self.mock_request_context({"id": "user_123"}) as mock_client:
            user_data = {
                "email": "convenience@example.com",
                "password": "test_password",
                "first_name": "Test",
                "last_name": "User",
            }
            user = self.sdk.register(**user_data)
            assert "id" in user

        # Test team convenience methods
        with self.mock_request_context({"id": "team_123"}) as mock_client:
            team_data = {"name": "convenience_team"}
            team = self.sdk.teams.create(team_data)
            assert "id" in team
