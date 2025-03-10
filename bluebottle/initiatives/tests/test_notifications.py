from bluebottle.initiatives.messages import InitiativeSubmittedStaffMessage
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.offices.tests.factories import LocationFactory, OfficeSubRegionFactory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase


class ReviewerNotificationTestCase(NotificationTestCase):
    message_class = InitiativeSubmittedStaffMessage

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
        self.assertSubject('A new initiative is ready to be reviewed.')
        self.assertBodyContains('has been submitted by Henk and is waiting for a review')
        self.assertActionLink(self.obj.get_admin_url())
        self.assertActionTitle('View the initiative')

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
        self.assertSubject("A new initiative is ready to be reviewed.")
        self.assertBodyContains(
            "has been submitted by Henk and is waiting for a review"
        )
        self.assertActionLink(self.obj.get_admin_url())
        self.assertActionTitle("View the initiative")
