from bluebottle.deeds.tests.factories import DeedParticipantFactory

from bluebottle.updates.messages import (
    OwnerNotification, FollowersNotification, ParentNotification
)
from bluebottle.updates.tests.factories import UpdateFactory

from bluebottle.test.utils import NotificationTestCase


class FollowerNotificationTestCase(NotificationTestCase):
    message_class = FollowersNotification

    def setUp(self):
        super().setUp()
        self.obj = UpdateFactory.create()
        self.participants = DeedParticipantFactory.create_batch(2, activity=self.obj.activity)
        self.create()

    def test_subject(self):
        self.assertSubject(f"Update from '{self.obj.activity.title}'")

    def test_recipients(self):
        self.assertRecipients([participant.user for participant in self.participants])


class OwnerNotificationTestCase(NotificationTestCase):
    message_class = OwnerNotification

    def setUp(self):
        super().setUp()
        self.obj = UpdateFactory.create()
        self.create()

    def test_subject(self):
        self.assertSubject(f"You have a new update on '{self.obj.activity.title}'")

    def test_recipients(self):
        self.assertRecipients([self.obj.activity.owner])


class ParentNotificationTestCase(NotificationTestCase):
    message_class = ParentNotification

    def setUp(self):
        super().setUp()
        self.obj = UpdateFactory.create(parent=UpdateFactory.create())
        self.create()

    def test_subject(self):
        self.assertSubject(f"You have a new reply on '{self.obj.activity.title}'")

    def test_recipients(self):
        self.assertRecipients([self.obj.parent.author])
