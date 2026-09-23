from builtins import str
from django.core import mail

from bluebottle.activities.messages.activity_manager import ActivityRejectedNotification
from bluebottle.activities.tests.factories import RemoteMemberFactory
from bluebottle.time_based.tests.factories import DateActivityFactory
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.deeds.messages import ParticipantJoinedNotification
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class NotificationEffectsTestCase(BluebottleTestCase):

    def test_notification_effect(self):
        user = BlueBottleUserFactory.create(
            email='faal@haas.nl'
        )
        activity = DateActivityFactory.create(
            title='Bound to fail',
            owner=user
        )
        subject = 'Your activity "Bound to fail" has been rejected'
        effect = NotificationEffect(ActivityRejectedNotification)(activity)

        self.assertEqual(str(effect), 'Message {} to faal@haas.nl'.format(subject))
        effect.post_save()

        self.assertEqual(mail.outbox[0].subject, subject)

    def test_valid_local_user(self):
        activity = DeedFactory.create(title='Bound to fail')
        participant = DeedParticipantFactory.create(
            activity=activity, user=BlueBottleUserFactory.create(), remote_user=None
        )

        effect = NotificationEffect(ParticipantJoinedNotification)(participant)
        self.assertEqual(effect.is_valid, True)

    def test_invalid_remote_user(self):
        activity = DeedFactory.create(title='Bound to fail')
        participant = DeedParticipantFactory.create(
            activity=activity, user=None, remote_user=RemoteMemberFactory.create()
        )
        effect = NotificationEffect(ParticipantJoinedNotification)(participant)
        self.assertEqual(effect.is_valid, False)
