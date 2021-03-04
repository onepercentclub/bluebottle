from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase


class DeedNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.obj = DeedFactory.create(
            title="Save the world!"
        )


class ParticipantNotificationTestCase(NotificationTestCase):

    def setUp(self):
        self.supporter = BlueBottleUserFactory.create()
        self.owner = BlueBottleUserFactory.create()
        self.activity = DeedFactory.create(
            title="Save the world!",
            owner=self.owner
        )
        self.obj = DeedParticipantFactory.create(
            activity=self.activity,
            user=self.supporter
        )
