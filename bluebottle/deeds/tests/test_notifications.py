from datetime import timedelta

from django.utils.timezone import now

from bluebottle.deeds.messages import DeedDateChangedNotification
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
        self.next_week = now() + timedelta(days=7)
        self.activity = DeedFactory.create(
            title="Save the world!",
            owner=self.owner,
            start=self.next_week,
            end=None
        )
        self.obj = DeedParticipantFactory.create(
            activity=self.activity,
            user=self.supporter
        )

    def test_deed_date_changed_notification(self):
        self.obj = self.activity
        self.message_class = DeedDateChangedNotification
        self.create()
        self.assertRecipients([self.supporter])
        self.assertSubject('The date for the activity "Save the world!" has changed')
        self.assertBodyContains(
            'The start and/or end date of the activity "Save the world!", '
            'in which you are participating, has changed.')
        self.assertBodyContains('Start: {}'.format(self.next_week.strftime('%x')))
        self.assertBodyContains('End: Runs indefinitely')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('View activity')
