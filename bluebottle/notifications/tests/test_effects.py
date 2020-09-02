from django.core import mail

from bluebottle.events.messages import EventRejectedOwnerMessage
from bluebottle.events.tests.factories import EventFactory
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class MockEffect(object):

    instance = None

    def __init__(self, instance):
        self.instance = instance


class NotificationEffectsTestCase(BluebottleTestCase):

    def test_notification_effect(self):
        user = BlueBottleUserFactory.create(
            email='faal@haas.nl'
        )
        event = EventFactory.create(
            title='Bound to fail',
            owner=user
        )
        effect = MockEffect(event)
        subject = 'Your event "Bound to fail" has been rejected'
        effect = NotificationEffect(EventRejectedOwnerMessage)(effect)
        self.assertEqual(unicode(effect), 'Message {} to faal@haas.nl'.format(subject))
        effect.execute()
        self.assertEqual(mail.outbox[0].subject, subject)
