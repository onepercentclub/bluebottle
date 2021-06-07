from bluebottle.initiatives.messages import InitiativeSubmittedStaffMessage
from bluebottle.initiatives.tests.factories import InitiativeFactory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase


class ReviewerNotificationTestCase(NotificationTestCase):

    def test_submitted_notification(self):
        staff = BlueBottleUserFactory.create(
            email='staff@example.com',
            is_staff=True,
            submitted_initiative_notifications=True
        )
        initiator = BlueBottleUserFactory.create(first_name='Henk', last_name='qui Penk')
        self.obj = InitiativeFactory.create(title="Save the world!", owner=initiator)
        self.obj.states.submit(save=True)
        self.message_class = InitiativeSubmittedStaffMessage
        self.create()
        self.assertRecipients([staff])
        self.assertSubject('A new initiative is ready to be reviewed.')
        self.assertBodyContains('has been submitted by Henk and is waiting for a review')
        self.assertActionLink(self.obj.get_admin_url())
        self.assertActionTitle('View the initiative')
