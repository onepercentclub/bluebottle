import os

from django.core import mail
from django.test import override_settings

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.notifications.messages import TransitionMessage
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from django.utils.translation import ugettext_lazy as _


class TestMessage(TransitionMessage):
    subject = _("Test message for {title}")
    template = 'test_messages/test_message'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        return [self.obj.owner]


class AnotherTestMessage(TransitionMessage):
    subject = _("Test message")
    template = 'test_message'


@override_settings(
    LOCALE_PATHS=[os.path.join(os.path.dirname(__file__), 'locale')]
)
class MessageTestCase(BluebottleTestCase):

    def test_message_subject_with_context(self):
        message = TestMessage(InitiativeFactory(title='Some title'))
        subject = message.get_subject()
        self.assertEqual(subject, "Test message for Some title")

    def test_message_subject_without_context(self):
        message = AnotherTestMessage(InitiativeFactory(title='Some title'))
        subject = message.get_subject()
        self.assertEqual(subject, "Test message")

    def test_translated_message_subject_with_context(self):
        message = TestMessage(InitiativeFactory(title='Some title'))
        subject = message.get_subject('nl')
        self.assertEqual(subject, "Test bericht voor Some title")

    def test_translated_messages(self):
        dutchy = BlueBottleUserFactory.create(primary_language='nl')
        message = TestMessage(InitiativeFactory(owner=dutchy, title='Some title'))
        messages = message.get_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].subject, "Test bericht voor Some title")

    def test_send_messages(self):
        dutchy = BlueBottleUserFactory.create()
        message = TestMessage(InitiativeFactory(owner=dutchy, title='Some title'))
        message.compose_and_send()
        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Test message for Some title")
        self.assertTrue('This is a test message' in email.body)
