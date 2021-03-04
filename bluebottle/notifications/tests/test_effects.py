from builtins import str
from django.core import mail

from bluebottle.activities.messages import ActivityRejectedNotification
from bluebottle.time_based.tests.factories import DateActivityFactory
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
