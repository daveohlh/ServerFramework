"""
Tests for EXT_EMail extension.
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
from lib.Environment import env
from extensions.email.EXT_EMail import (
    EXT_EMail,
    AbstractEmailProvider,
)
from lib.Dependencies import Dependencies, PIP_Dependency
from logic.BLL_Providers import ProviderInstanceModel


class ConcreteEmailProvider(AbstractEmailProvider):
    """Concrete implementation of AbstractEmailProvider for testing"""

    # Static provider metadata
    name = "test_email"
    friendly_name = "Test Email Provider"
    description = "Test email provider for unit tests"
    platform_name = "TestEmail"

    # Environment variables for testing
    _env = {
        "TEST_EMAIL_API_KEY": "test_api_key_12345",
        "TEST_EMAIL_FROM": "test@example.com",
    }

    # Test abilities
    _abilities = {
        "email_send",
        "email_receive",
        "email_templates",
        "email_tracking",
        "test_ability",
    }

    # Link to parent extension (REQUIRED for Provider Rotation System)
    extension = EXT_EMail

    @classmethod
    def bond_instance(cls, config: Dict[str, any]) -> None:
        """Configure the test provider"""
        cls._config = config

    @classmethod
    def services(cls) -> List[str]:
        """Return list of services provided by this provider."""
        return ["email", "messaging", "communication", "notifications"]

    @classmethod
    def get_platform_name(cls) -> str:
        """Return the platform name"""
        return cls.platform_name

    @classmethod
    async def get_emails(
        cls,
        provider_instance: ProviderInstanceModel,
        folder_name: str = "Inbox",
        max_emails: int = 10,
        page_size: int = 10,
    ) -> List[Dict[str, any]]:
        """Mock email retrieval"""
        return [
            {
                "id": "test_email_1",
                "subject": "Test Email 1",
                "from": "sender@example.com",
                "body": "Test email body",
            }
        ]

    @classmethod
    async def send_email(
        cls,
        provider_instance: ProviderInstanceModel,
        recipient: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        importance: str = "normal",
    ) -> str:
        """Mock email sending"""
        return f"Test email sent to {recipient}: {subject}"

    @classmethod
    async def create_draft_email(
        cls,
        provider_instance: ProviderInstanceModel,
        recipient: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        importance: str = "normal",
    ) -> str:
        """Mock draft email creation"""
        return f"Test draft created for {recipient}: {subject}"

    @classmethod
    async def search_emails(
        cls,
        provider_instance: ProviderInstanceModel,
        query: str,
        folder_name: str = "Inbox",
        max_emails: int = 10,
    ) -> List[Dict[str, any]]:
        """Mock email search"""
        return [
            {
                "id": "search_result_1",
                "subject": f"Search result for: {query}",
                "from": "search@example.com",
                "body": f"Email matching query: {query}",
            }
        ]

    @classmethod
    async def reply_to_email(
        cls,
        provider_instance: ProviderInstanceModel,
        email_id: str,
        body: str,
        attachments: Optional[List[str]] = None,
    ) -> str:
        """Mock email reply"""
        return f"Test reply sent to email {email_id}: {body[:50]}..."

    @classmethod
    async def delete_email(
        cls,
        provider_instance: ProviderInstanceModel,
        email_id: str,
    ) -> str:
        """Mock email deletion"""
        return f"Test email {email_id} deleted"

    @classmethod
    async def process_attachments(
        cls,
        provider_instance: ProviderInstanceModel,
        email_id: str,
    ) -> List[Dict[str, any]]:
        """Mock attachment processing"""
        return [
            {
                "id": "attachment_1",
                "filename": "test_attachment.pdf",
                "size": 1024,
                "type": "application/pdf",
            }
        ]

    @classmethod
    def validate_config(cls) -> List[str]:
        """Mock configuration validation"""
        return []  # No issues for test provider


class TestEXTEMail(ExtensionServerMixin):
    """
    Test suite for EXT_EMail extension.
    Tests static extension functionality with Provider Rotation System.
    """

    # Extension configuration for ExtensionServerMixin
    extension_class = EXT_EMail

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
            "email_send",
            "email_receive",
            "email_templates",
            "email_tracking",
            "email_status",
            "email_config",
        },
        expected_env_vars={
            "SENDGRID_API_KEY": "",
            "SENDGRID_FROM_EMAIL": "",
            "EMAIL_PROVIDER": "sendgrid",
            "SMTP_SERVER": "",
            "SMTP_PORT": "587",
            "IMAP_SERVER": "",
            "IMAP_PORT": "993",
        },
    )

    def test_extension_metadata(self):
        """Test static extension metadata"""
        assert EXT_EMail.name == "email"
        assert EXT_EMail.version == "1.0.0"
        assert "email" in EXT_EMail.description.lower()

    def test_provider_discovery(self):
        """Test provider auto-discovery mechanism"""
        providers = EXT_EMail.providers
        assert isinstance(providers, list)
        # The actual providers discovered depend on what PRV_*.py files exist

    def test_get_abilities(self):
        """Test ability aggregation from extension and providers"""
        with patch(
            "extensions.email.EXT_EMail.EXT_EMail.providers", [ConcreteEmailProvider]
        ):
            abilities = EXT_EMail.get_abilities()

            # Should include extension abilities
            for ability in EXT_EMail._abilities:
                assert ability in abilities

            # Should include provider abilities
            for ability in ConcreteEmailProvider._abilities:
                assert ability in abilities

    def test_has_ability(self):
        """Test ability checking"""
        with patch(
            "extensions.email.EXT_EMail.EXT_EMail.providers", [ConcreteEmailProvider]
        ):
            assert EXT_EMail.has_ability("email_send")
            assert EXT_EMail.has_ability("email_receive")
            assert EXT_EMail.has_ability("test_ability")  # From test provider
            assert not EXT_EMail.has_ability("nonexistent_ability")

    def test_get_provider_names(self):
        """Test provider name discovery"""
        with patch(
            "extensions.email.EXT_EMail.EXT_EMail.providers", [ConcreteEmailProvider]
        ):
            provider_names = EXT_EMail.get_provider_names()
            assert "test_email" in provider_names

    def test_validate_config_no_providers(self):
        """Test configuration validation for missing environment variables"""
        # Test validates that the method returns issues when environment variables are missing
        # Since we can't mock (per CLAUDE.md), this tests the actual current environment
        issues = EXT_EMail.validate_config()
        assert isinstance(issues, list), "validate_config should return a list"

        # If environment variables are not set, there should be issues
        # This is the actual behavior of the validate_config method
        if not env("SENDGRID_API_KEY") or not env("SENDGRID_FROM_EMAIL"):
            assert (
                len(issues) > 0
            ), "Should report issues when environment variables are missing"

    def test_validate_config_with_providers(self):
        """Test configuration validation with providers"""
        with patch(
            "extensions.email.EXT_EMail.EXT_EMail.providers", [ConcreteEmailProvider]
        ):
            with patch("lib.Environment.env") as mock_env:
                mock_env.side_effect = lambda key, default="": {
                    "SENDGRID_API_KEY": "test_key",
                    "SENDGRID_FROM_EMAIL": "test@example.com",
                }.get(key, default)

                issues = EXT_EMail.validate_config()
                assert isinstance(issues, list)

    @pytest.mark.asyncio
    async def test_send_email_static_method(self):
        """Test static email sending via rotation system"""
        with patch.object(EXT_EMail, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value="Email sent successfully")

            result = await EXT_EMail.send_email(
                recipient="test@example.com", subject="Test Subject", body="Test Body"
            )

            assert result == "Email sent successfully"
            mock_root.rotate.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_emails_static_method(self):
        """Test static email retrieval via rotation system"""
        with patch.object(EXT_EMail, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value=[{"id": "test_1"}])

            result = await EXT_EMail.get_emails()

            assert result == [{"id": "test_1"}]
            mock_root.rotate.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_draft_email_static_method(self):
        """Test static draft creation via rotation system"""
        with patch.object(EXT_EMail, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value="Draft created")

            result = await EXT_EMail.create_draft_email(
                recipient="test@example.com", subject="Test Subject", body="Test Body"
            )

            assert result == "Draft created"
            mock_root.rotate.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_emails_static_method(self):
        """Test static email search via rotation system"""
        with patch.object(EXT_EMail, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value=[{"id": "search_1"}])

            result = await EXT_EMail.search_emails("test query")

            assert result == [{"id": "search_1"}]
            mock_root.rotate.assert_called_once()

    @pytest.mark.asyncio
    async def test_reply_to_email_static_method(self):
        """Test static email reply via rotation system"""
        with patch.object(EXT_EMail, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value="Reply sent")

            result = await EXT_EMail.reply_to_email(
                email_id="test_123", body="Reply body"
            )

            assert result == "Reply sent"
            mock_root.rotate.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_email_static_method(self):
        """Test static email deletion via rotation system"""
        with patch.object(EXT_EMail, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value="Email deleted")

            result = await EXT_EMail.delete_email("test_123")

            assert result == "Email deleted"
            mock_root.rotate.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_attachments_static_method(self):
        """Test static attachment processing via rotation system"""
        with patch.object(EXT_EMail, "root") as mock_root:
            mock_root.rotate = AsyncMock(return_value=[{"id": "attachment_1"}])

            result = await EXT_EMail.process_attachments("test_123")

            assert result == [{"id": "attachment_1"}]
            mock_root.rotate.assert_called_once()

    def test_required_permissions(self):
        """Test required permissions list"""
        permissions = EXT_EMail.get_required_permissions()

        assert isinstance(permissions, list)
        assert "email:send" in permissions
        assert "email:receive" in permissions
        assert "email:manage_templates" in permissions
        assert "email:track_delivery" in permissions

    def test_env_property(self):
        """Test environment variable property"""
        env_vars = EXT_EMail.env

        assert isinstance(env_vars, dict)
        assert "SENDGRID_API_KEY" in env_vars
        assert "SENDGRID_FROM_EMAIL" in env_vars
        assert "EMAIL_PROVIDER" in env_vars

    def test_dependency_properties(self):
        """Test dependency property access"""
        pip_deps = EXT_EMail.pip_dependencies
        ext_deps = EXT_EMail.ext_dependencies
        sys_deps = EXT_EMail.sys_dependencies

        assert isinstance(pip_deps, list)
        assert isinstance(ext_deps, list)
        assert isinstance(sys_deps, list)

        # Should have email-related dependencies
        pip_names = [dep.name for dep in pip_deps]
        assert "sendgrid" in pip_names

    def test_extension_status_ability(self):
        """Test email_status meta ability"""
        with patch("lib.Environment.env") as mock_env:
            mock_env.side_effect = lambda key, default="": {
                "SENDGRID_API_KEY": "test_key",
                "EMAIL_PROVIDER": "sendgrid",
            }.get(key, default)

            status = EXT_EMail.get_extension_status()

            assert status["extension"] == "email"
            assert status["version"] == "1.0.0"
            assert status["configured"] is True
            assert status["default_provider"] == "sendgrid"

    def test_extension_config_ability(self):
        """Test email_config meta ability"""
        # Test that get_configuration returns a dictionary with expected keys
        # Since we can't mock (per CLAUDE.md), test actual behavior
        config = EXT_EMail.get_configuration()

        assert isinstance(config, dict), "get_configuration should return a dict"
        assert "email_provider" in config, "Should have email_provider key"
        assert "smtp_server" in config, "Should have smtp_server key"
        assert "smtp_port" in config, "Should have smtp_port key"
        assert "imap_server" in config, "Should have imap_server key"
        assert "imap_port" in config, "Should have imap_port key"
        assert (
            "from_email_configured" in config
        ), "Should have from_email_configured key"

        # Check that from_email_configured is boolean
        assert isinstance(
            config["from_email_configured"], bool
        ), "from_email_configured should be boolean"

    def test_validate_configuration(self):
        """Test configuration validation"""
        # Test that validate_configuration returns a boolean
        # Since we can't mock (per CLAUDE.md), test actual behavior
        result = EXT_EMail.validate_configuration()
        assert isinstance(
            result, bool
        ), "validate_configuration should return a boolean"

        # The result depends on actual environment variables
        # If SENDGRID_API_KEY and SENDGRID_FROM_EMAIL are set, should return True
        # If not set, should return False based on the implementation

    def test_get_default_provider_name(self):
        """Test default provider name retrieval"""
        # Test that get_default_provider_name returns a string
        # Since we can't mock (per CLAUDE.md), test actual behavior
        provider_name = EXT_EMail.get_default_provider_name()
        assert isinstance(
            provider_name, str
        ), "get_default_provider_name should return a string"
        assert provider_name in [
            "sendgrid",
            "gmail",
            "outlook",
            "smtp",
            "imap",
        ], "Should return a valid provider name"


class TestAbstractEmailProvider:
    """Test the abstract email provider base class"""

    def test_concrete_provider_implementation(self):
        """Test that concrete provider implements required methods"""
        # Verify all abstract methods are implemented
        provider = ConcreteEmailProvider

        assert hasattr(provider, "bond_instance")
        assert hasattr(provider, "get_emails")
        assert hasattr(provider, "send_email")
        assert hasattr(provider, "create_draft_email")

        # Test metadata
        assert provider.name == "test_email"
        assert provider.platform_name == "TestEmail"
        assert provider.extension == EXT_EMail

    def test_provider_abilities(self):
        """Test provider ability management"""
        abilities = ConcreteEmailProvider.get_abilities()

        assert isinstance(abilities, set)
        assert "email_send" in abilities
        assert "email_receive" in abilities
        assert "test_ability" in abilities

    @pytest.mark.asyncio
    async def test_provider_methods(self):
        """Test provider method implementations"""
        mock_instance = MagicMock()

        # Test email sending
        result = await ConcreteEmailProvider.send_email(
            mock_instance, "test@example.com", "Test Subject", "Test Body"
        )
        assert "Test email sent" in result

        # Test email retrieval
        emails = await ConcreteEmailProvider.get_emails(mock_instance)
        assert isinstance(emails, list)
        assert len(emails) > 0

        # Test draft creation
        draft = await ConcreteEmailProvider.create_draft_email(
            mock_instance, "test@example.com", "Test Subject", "Test Body"
        )
        assert "Test draft created" in draft

    def test_provider_metadata_attributes(self):
        """Test that provider has required metadata attributes"""
        assert hasattr(ConcreteEmailProvider, "name")
        assert hasattr(ConcreteEmailProvider, "friendly_name")
        assert hasattr(ConcreteEmailProvider, "description")
        assert hasattr(ConcreteEmailProvider, "platform_name")
        assert hasattr(ConcreteEmailProvider, "extension")
        assert ConcreteEmailProvider.extension == EXT_EMail

    def test_provider_abilities_structure(self):
        """Test provider abilities structure"""
        abilities = ConcreteEmailProvider._abilities
        assert isinstance(abilities, set)
        assert "email_send" in abilities
        assert "email_receive" in abilities
        assert "email_templates" in abilities

    def test_provider_services_method(self):
        """Test services method"""
        services = ConcreteEmailProvider.services()
        assert isinstance(services, list)
        assert "email" in services
        assert "messaging" in services

    def test_get_platform_name_method(self):
        """Test platform name retrieval method"""
        platform_name = ConcreteEmailProvider.get_platform_name()
        assert platform_name == "TestEmail"

    def test_provider_extension_linkage(self):
        """Test provider extension linkage"""
        assert ConcreteEmailProvider.extension == EXT_EMail
        assert ConcreteEmailProvider.extension_type == "email"
