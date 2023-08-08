from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.test.utils import TriggerTestCase
from bluebottle.updates.messages import OwnerNotification, FollowersNotification, ParentNotification
from bluebottle.updates.tests.factories import UpdateFactory


class DeedTriggersTestCase(TriggerTestCase):
    factory = UpdateFactory

    def setUp(self):
        self.defaults = {
            'activity': DeedFactory.create(),
        }
        super().setUp()

    def create(self):
        self.model = self.factory.build(**self.defaults)

    def test_create_notify(self):
        DeedParticipantFactory.create(activity=self.defaults['activity'])
        self.defaults['author'] = self.defaults['activity'].owner
        self.defaults['notify'] = True
        self.create()

        with self.execute():
            self.assertNotificationEffect(FollowersNotification)
            self.assertNoNotificationEffect(OwnerNotification)

    def test_create_no_notify(self):
        DeedParticipantFactory.create(activity=self.defaults['activity'])
        self.defaults['author'] = self.defaults['activity'].owner
        self.create()

        with self.execute():
            self.assertNoNotificationEffect(FollowersNotification)
            self.assertNoNotificationEffect(OwnerNotification)

    def test_create_parent(self):
        self.defaults['parent'] = UpdateFactory.create(activity=self.defaults['activity'])
        self.create()

        with self.execute():
            self.assertNotificationEffect(ParentNotification)
            self.assertNotificationEffect(OwnerNotification)

    def test_create_no_parent(self):
        self.create()

        with self.execute():
            self.assertNoNotificationEffect(ParentNotification)
            self.assertNotificationEffect(OwnerNotification)

    def test_create_owner(self):
        self.create()

        with self.execute():
            self.assertNotificationEffect(OwnerNotification)

    def test_create_owner_is_author(self):
        self.defaults['author'] = self.defaults['activity'].owner
        self.create()

        with self.execute():
            self.assertNoNotificationEffect(OwnerNotification)
