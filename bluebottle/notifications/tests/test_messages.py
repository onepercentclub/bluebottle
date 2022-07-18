import os

from django.core import mail
from django.test import override_settings

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.notifications.messages import TransitionMessage
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from django.utils.translation import gettext_lazy as _


class TestMessage(TransitionMessage):
    subject = _("Test message for {title}")
    template = 'test_messages/test_message'
    context = {
        'title': 'title'
    }

    def get_recipients(self):
        yield self.obj.owner


class AnotherTestMessage(TransitionMessage):
    subject = _("Test message")
    template = 'test_messages/test_message'

    def get_recipients(self):
        return [
            self.obj.owner,
            self.obj.reviewer
        ]


@override_settings(
    LOCALE_PATHS=[os.path.join(os.path.dirname(__file__), 'locale')]
)
class MessageTestCase(BluebottleTestCase):

    def test_message_subject_with_context(self):
        english = BlueBottleUserFactory.create(primary_language='en')
        message = TestMessage(InitiativeFactory(title='Some title', owner=english))
        messages = list(message.get_messages())
        self.assertEqual(messages[0].subject, "Test message for Some title")

    def test_message_body_escaped(self):
        user = BlueBottleUserFactory.create(primary_language='en', first_name="<h1>First Name</h2>")
        TestMessage(InitiativeFactory(title='Some title', owner=user)).compose_and_send()
        message = mail.outbox[0]
        self.assertTrue('Hi &lt;h1&gt;First Name&lt;/h2&gt;,' in message.alternatives[0][0])

    def test_message_subject_without_context(self):
        english = BlueBottleUserFactory.create(primary_language='en')
        message = AnotherTestMessage(InitiativeFactory(title='Some title', owner=english))
        messages = list(message.get_messages())
        self.assertEqual(messages[0].subject, "Test message")

    def test_translated_message_subject_with_context(self):
        dutch = BlueBottleUserFactory.create(primary_language='nl')
        message = TestMessage(InitiativeFactory(title='Some title', owner=dutch))
        messages = list(message.get_messages())
        self.assertEqual(messages[0].subject, "Test bericht voor Some title")

    def test_translated_messages(self):
        dutch = BlueBottleUserFactory.create(primary_language='nl')
        message = TestMessage(InitiativeFactory(owner=dutch, title='Some title'))
        messages = list(message.get_messages())
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].subject, "Test bericht voor Some title")

    def test_send_translated_messages(self):
        english = BlueBottleUserFactory.create(primary_language='en')
        dutch = BlueBottleUserFactory.create(primary_language='nl')
        initiative = InitiativeFactory(owner=dutch, reviewer=english, title='Some title')
        mail.outbox = []
        message = AnotherTestMessage(initiative)

        message.compose_and_send()
        self.assertEqual(len(mail.outbox), 2)
        for message in mail.outbox:
            if message.to[0] == english.email:
                self.assertEqual(message.subject, 'Test message')
                self.assertTrue('This is a test message' in message.body)
            if message.to[0] == dutch.email:
                self.assertEqual(message.subject, 'Test bericht')
