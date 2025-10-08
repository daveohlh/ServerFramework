# Set default test configuration for all test classes

from AbstractTest import ClassOfTestsConfig, CategoryOfTest
from logic.AbstractBLLTest import AbstractBLLTest
from extensions.AbstractEXTTest import ExtensionServerMixin
from extensions.email.EXT_EMail import EXT_EMail
from lib.Environment import env
from logic.AbstractLogicManager import AbstractBLLManager


AbstractBLLTest.test_config = ClassOfTestsConfig(
    categories=[CategoryOfTest.LOGIC, CategoryOfTest.EXTENSION]
)


class TestEmailManager(AbstractBLLTest, ExtensionServerMixin):
    """
    Test class for the Email Manager extension.
    This class inherits from AbstractBLLTest and ExtensionServerMixin to provide
    a framework for testing the email functionality in the server.
    """

    class_under_test = AbstractBLLManager
    extension_class = EXT_EMail

    create_fields = {}
    update_fields = {}
    unique_fields = {}

    def test_send_email_on_invitation(self, admin_a, team_a, model_registry):
        """
        Sends an email when an invitation-invitee is created.

        Args:
            entity: The invitee object containing invitation and details for the email.
        """

        from logic.BLL_Auth import InvitationManager

        with InvitationManager(
            model_registry=model_registry,
            requester_id=admin_a.id,
        ) as manager:
            # Create an invitation
            invitation = manager.create(
                team_id=team_a.id,
                role_id=env("USER_ROLE_ID"),
                email="dj.ecex@gmail.com",
            )

        assert invitation is not None, "Invitation should be created successfully"
