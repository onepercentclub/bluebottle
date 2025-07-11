from datetime import timedelta, date
from django.utils import formats

from bluebottle.deeds.messages import (
    DeedDateChangedNotification, ParticipantJoinedNotification
)

from bluebottle.activities.messages.participant import (
    ParticipantWithdrewConfirmationNotification
)
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
        self.next_week = date.today() + timedelta(days=7)
        self.next_month = date.today() + timedelta(days=31)

        self.activity = DeedFactory.create(
            title="Save the world!",
            owner=self.owner,
            start=self.next_week,
            end=self.next_month,
        )
        self.obj = DeedParticipantFactory.create(
            activity=self.activity,
            user=self.supporter
        )

    def test_deed_date_changed_notification(self):
        self.activity.end = None

        self.obj = self.activity
        self.message_class = DeedDateChangedNotification

        self.create()

        self.assertRecipients([self.supporter])
        self.assertSubject('The date for the activity "Save the world!" has changed')
        self.assertBodyContains(
            'The start and/or end date of the activity "Save the world!", '
            'in which you are participating, has changed.')
        self.assertBodyContains(f'Start: {formats.date_format(self.next_week, "SHORT_DATE_FORMAT")}')
        self.assertBodyContains('End: Runs indefinitely')
        self.assertActionLink(self.activity.get_absolute_url())
        self.assertActionTitle('View activity')

    def test_joined(self):
        self.message_class = ParticipantJoinedNotification

        self.create()

        self.assertRecipients([self.supporter])
        self.assertSubject('You have joined the activity "Save the world!"')

        self.assertHtmlBodyContains('You joined an activity on <b>Test</b>')

        self.assertBodyContains(f'Ends on {formats.date_format(self.next_month, "SHORT_DATE_FORMAT")}')

    def test_withdrew_confirmation(self):
        self.message_class = ParticipantWithdrewConfirmationNotification

        self.create()

        self.assertRecipients([self.supporter])
        self.assertSubject('You have withdrawn from the activity "Save the world!"')

        self.assertHtmlBodyContains('You have withdrawn from an activity on <b>Test</b>')
