from bluebottle.initiatives.messages.initiator import InitiativeSubmittedInitiatorMessage, \
    InitiativeNeedsWorkInitiatorMessage, InitiativeRejectedInitiatorMessage, InitiativeApprovedInitiatorMessage, \
    InitiativePublishedInitiatorMessage
from bluebottle.initiatives.messages.reviewer import InitiativeSubmittedReviewerMessage, \
    InitiativePublishedReviewerMessage
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.offices.tests.factories import LocationFactory, OfficeSubRegionFactory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase


class ReviewerNotificationTestCase(NotificationTestCase):
    message_class = InitiativeSubmittedReviewerMessage

    def test_submitted_notification_staff(self):
        staff = BlueBottleUserFactory.create(
            email='staff@example.com',
            is_staff=True,
            submitted_initiative_notifications=True
        )
        initiator = BlueBottleUserFactory.create(first_name='Henk', last_name='qui Penk')
        self.obj = InitiativeFactory.create(title="Save the world!", owner=initiator)
        self.obj.states.submit(save=True)

        self.create()

        self.assertRecipients([staff])
        self.assertSubject('A new initiative is ready to be reviewed on Test')
        self.assertBodyContains('has been submitted by Henk qui Penk')
        self.assertActionLink(self.obj.get_admin_url())
        self.assertActionTitle('View initiative')

    def test_submitted_notification_region(self):
        region = OfficeSubRegionFactory.create()
        current_region = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True,
        )
        current_region.subregion_manager.add(region)

        another = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True,
        )
        another.subregion_manager.add(OfficeSubRegionFactory.create())

        no_region = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True,
        )

        initiator = BlueBottleUserFactory.create(
            first_name="Henk", last_name="qui Penk"
        )

        self.obj = InitiativeFactory.create(
            title="Save the world!",
            owner=initiator,
            location=LocationFactory.create(subregion=region),
        )
        self.obj.states.submit(save=True)
        self.create()
        self.assertRecipients([current_region, no_region])
        self.assertSubject("A new initiative is ready to be reviewed on Test")
        self.assertBodyContains('has been submitted by Henk qui Penk')
        self.assertActionLink(self.obj.get_admin_url())
        self.assertActionTitle("View initiative")


class InitiativeNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.obj = InitiativeFactory.create()
        self.reviewer = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True
        )

    def test_initiative_submitted_reviewer_message(self):
        self.message_class = InitiativeSubmittedReviewerMessage
        self.create()
        self.assertRecipients([self.reviewer])
        self.assertSubject('A new initiative is ready to be reviewed on Test')
        self.assertBodyContains('Please take a moment to review this initiative')
        self.assertActionLink(self.obj.get_admin_url())
        self.assertActionTitle('View initiative')

    def test_initiative_published_reviewer_message(self):
        self.message_class = InitiativePublishedReviewerMessage
        self.create()
        self.assertRecipients([self.reviewer])
        self.assertSubject('A new initiative has been published on Test!')
        self.assertBodyContains('has been successfully published')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View initiative')

    def test_initiative_submitted_initiator_message(self):
        self.message_class = InitiativeSubmittedInitiatorMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('You submitted an initiative on Test')
        self.assertBodyContains('The platform manager will review your initiative')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View initiative')

    def test_initiative_published_initiator_message(self):
        self.message_class = InitiativePublishedInitiatorMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your initiative on Test has been published!')
        self.assertBodyContains('Nice work! Your initiative')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View initiative')

    def test_initiative_approved_initiator_message(self):
        self.message_class = InitiativeApprovedInitiatorMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your initiative on Test has been approved!')
        self.assertBodyContains('Good news, your initiative')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View initiative')

    def test_initiative_needs_work_initiator_message(self):
        self.message_class = InitiativeNeedsWorkInitiatorMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('The initiative you submitted on Test needs work')
        self.assertBodyContains(
            'The platform manager will be in contact to help you make some changes to your initiative'
        )
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View initiative')

    def test_initiative_rejected_initiator_message(self):
        self.message_class = InitiativeRejectedInitiatorMessage
        self.create()
        self.assertRecipients([self.obj.owner])
        self.assertSubject('Your initiative on Test has been rejected')
        self.assertBodyContains('Unfortunately your initiative')
        self.assertActionLink(self.obj.get_absolute_url())
        self.assertActionTitle('View initiative')
