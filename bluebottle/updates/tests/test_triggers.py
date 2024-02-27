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
        participants = DeedParticipantFactory.create_batch(3, activity=self.defaults['activity'])
        DeedParticipantFactory.create(
            activity=self.defaults['activity'], user=self.defaults['activity'].owner
        )
        self.defaults['author'] = self.defaults['activity'].owner
        self.defaults['notify'] = True
        self.create()

        with self.execute():
            self.assertNotificationEffect(
                FollowersNotification, [participant.user for participant in participants]
            )
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
            self.assertNotificationEffect(ParentNotification, [self.defaults['parent'].author])
            self.assertNotificationEffect(OwnerNotification, [self.defaults['activity'].owner])

    def test_create_no_parent(self):
        self.create()

        with self.execute():
            self.assertNoNotificationEffect(ParentNotification)
            self.assertNotificationEffect(OwnerNotification, [self.defaults['activity'].owner])

    def test_create_owner(self):
        self.create()

        with self.execute():
            self.assertNotificationEffect(OwnerNotification, [self.defaults['activity'].owner])

    def test_create_owner_is_author(self):
        self.defaults['author'] = self.defaults['activity'].owner
        self.create()

        with self.execute():
            self.assertNoNotificationEffect(OwnerNotification)
