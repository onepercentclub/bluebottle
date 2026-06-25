from datetime import date, timedelta

from django.core import mail
from moneyed import Money

from bluebottle.activities.forms import ActivityAcceptedForm, ActivityNeedsWorkForm, ActivityRejectedForm
from bluebottle.activities.messages.activity_manager import (
    ActivityApprovedNotification,
    ActivityNeedsWorkNotification,
    ActivityRejectedNotification,
)
from bluebottle.collect.models import CollectActivity
from bluebottle.collect.tests.factories import CollectActivityFactory
from bluebottle.deeds.models import Deed
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.funding.forms import (
    FundingAcceptedForm,
    FundingNeedsWorkForm,
    FundingRejectedForm,
)
from bluebottle.funding.messages.funding.activity_manager import (
    FundingApprovedMessage,
    FundingNeedsWorkMessage,
    FundingRejectedMessage,
)
from bluebottle.funding.models import Funding
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.fsm.triggers import TransitionTrigger
from bluebottle.grant_management.forms import (
    GrantApplicationApproveForm,
    GrantApplicationNeedsWorkForm,
    GrantApplicationRejectedForm,
)
from bluebottle.grant_management.messages.activity_manager import (
    GrantApplicationApprovedMessage,
    GrantApplicationNeedsWorkMessage,
    GrantApplicationRejectedMessage,
)
from bluebottle.grant_management.models import GrantApplication
from bluebottle.grant_management.tests.factories import (
    GrantApplicationFactory,
    GrantDepositFactory,
    GrantFundFactory,
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, TriggerTestCase
from bluebottle.time_based.forms import RegistrationAcceptForm, RegistrationRejectForm
from bluebottle.time_based.messages.registrations import (
    UserRegistrationAcceptedNotification,
    UserRegistrationRejectedNotification,
)
from bluebottle.time_based.models import DateActivity, DateRegistration
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateRegistrationFactory,
)


CUSTOM_MESSAGE = 'Please update the description before we can continue.'
CUSTOM_MESSAGE_HTML = '<p>Please <strong>update</strong> the description before we can continue.</p>'
ACTIVITY_TITLE = 'Community garden'


def _create_test_object(case):
    factory = case['factory']
    if factory is DateRegistrationFactory:
        activity = DateActivityFactory.create(title=ACTIVITY_TITLE, slots=[])
        return factory.create(activity=activity)
    return factory.create(title=ACTIVITY_TITLE)


def _message_cases():
    return [
        {
          'label': 'date_activity_approved',
          'factory': DateActivityFactory,
          'message': ActivityApprovedNotification,
          'default_snippet': 'Good news, your activity',
      },
      {
          'label': 'date_activity_rejected',
          'factory': DateActivityFactory,
          'message': ActivityRejectedNotification,
          'default_snippet': 'Unfortunately your activity',
      },
      {
          'label': 'date_activity_needs_work',
          'factory': DateActivityFactory,
          'message': ActivityNeedsWorkNotification,
          'default_snippet': 'has been reviewed and needs work',
      },
      {
          'label': 'deed_approved',
          'factory': DeedFactory,
          'message': ActivityApprovedNotification,
          'default_snippet': 'Good news, your activity',
      },
      {
          'label': 'deed_rejected',
          'factory': DeedFactory,
          'message': ActivityRejectedNotification,
          'default_snippet': 'Unfortunately your activity',
      },
      {
          'label': 'deed_needs_work',
          'factory': DeedFactory,
          'message': ActivityNeedsWorkNotification,
          'default_snippet': 'has been reviewed and needs work',
      },
      {
          'label': 'collect_approved',
          'factory': CollectActivityFactory,
          'message': ActivityApprovedNotification,
          'default_snippet': 'Good news, your activity',
      },
      {
          'label': 'collect_rejected',
          'factory': CollectActivityFactory,
          'message': ActivityRejectedNotification,
          'default_snippet': 'Unfortunately your activity',
      },
      {
          'label': 'collect_needs_work',
          'factory': CollectActivityFactory,
          'message': ActivityNeedsWorkNotification,
          'default_snippet': 'has been reviewed and needs work',
      },
      {
          'label': 'funding_approved',
          'factory': FundingFactory,
          'message': FundingApprovedMessage,
          'default_snippet': 'has been approved',
      },
      {
          'label': 'funding_rejected',
          'factory': FundingFactory,
          'message': FundingRejectedMessage,
          'default_snippet': 'Unfortunately your crowdfunding campaign',
      },
      {
          'label': 'funding_needs_work',
          'factory': FundingFactory,
          'message': FundingNeedsWorkMessage,
          'default_snippet': 'needs work',
      },
      {
          'label': 'grant_approved',
          'factory': GrantApplicationFactory,
          'message': GrantApplicationApprovedMessage,
          'default_snippet': 'Good news, your grant application',
      },
      {
          'label': 'grant_rejected',
          'factory': GrantApplicationFactory,
          'message': GrantApplicationRejectedMessage,
          'default_snippet': 'Unfortunately your grant application',
      },
      {
          'label': 'grant_needs_work',
          'factory': GrantApplicationFactory,
          'message': GrantApplicationNeedsWorkMessage,
          'default_snippet': 'needs work',
      },
      {
          'label': 'registration_accepted',
          'factory': DateRegistrationFactory,
          'message': UserRegistrationAcceptedNotification,
          'default_snippet': 'Good news, you have been accepted for the activity',
      },
      {
          'label': 'registration_rejected',
          'factory': DateRegistrationFactory,
          'message': UserRegistrationRejectedNotification,
          'default_snippet': 'you have not been selected for the activity',
      },
  ]


def _assert_custom_message_replaces_default(test_case, obj, message_class, default_snippet):
    default_message = message_class(obj)
    custom_message = message_class(obj, custom_message=CUSTOM_MESSAGE)
    recipient = default_message.get_recipients()[0]

    default_text = default_message.get_content_text(recipient)
    test_case.assertIn(default_snippet, default_text)

    notification_messages = list(custom_message.get_messages())
    test_case.assertEqual(len(notification_messages), 1)
    test_case.assertEqual(notification_messages[0].custom_message, CUSTOM_MESSAGE)

    mail.outbox = []
    custom_message.compose_and_send()
    test_case.assertEqual(len(mail.outbox), 1)
    test_case.assertIn(CUSTOM_MESSAGE, mail.outbox[0].body)
    test_case.assertNotIn(default_snippet, mail.outbox[0].body)


class CustomMessageNotificationTestCase(BluebottleTestCase):

    def test_custom_message_replaces_default_body(self):
        for case in _message_cases():
            with self.subTest(case=case['label']):
                obj = _create_test_object(case)
                _assert_custom_message_replaces_default(
                    self,
                    obj,
                    case['message'],
                    case['default_snippet'],
                )


def _notification_messages_for_transition(model, transition):
    messages = []
    for trigger in model.triggers.triggers:
        if not isinstance(trigger, TransitionTrigger):
            continue
        if trigger.transition != transition:
            continue
        for effect_cls in trigger.effects:
            message = getattr(effect_cls, 'message', None)
            if message:
                messages.append(message)
    return messages


def _form_has_custom_message_field(form_class):
    return 'custom_message' in form_class.base_fields


class TransitionCustomMessageCoverageTestCase(BluebottleTestCase):

    def test_transitions_with_custom_message_forms_have_notifications(self):
        cases = [
            (Deed, 'approve', ActivityAcceptedForm, ActivityApprovedNotification),
            (Deed, 'reject', ActivityRejectedForm, ActivityRejectedNotification),
            (Deed, 'request_changes', ActivityNeedsWorkForm, ActivityNeedsWorkNotification),
            (DateActivity, 'approve', ActivityAcceptedForm, ActivityApprovedNotification),
            (DateActivity, 'reject', ActivityRejectedForm, ActivityRejectedNotification),
            (DateActivity, 'request_changes', ActivityNeedsWorkForm, ActivityNeedsWorkNotification),
            (CollectActivity, 'approve', ActivityAcceptedForm, ActivityApprovedNotification),
            (CollectActivity, 'reject', ActivityRejectedForm, ActivityRejectedNotification),
            (CollectActivity, 'request_changes', ActivityNeedsWorkForm, ActivityNeedsWorkNotification),
            (Funding, 'approve', FundingAcceptedForm, FundingApprovedMessage),
            (Funding, 'reject', FundingRejectedForm, FundingRejectedMessage),
            (Funding, 'request_changes', FundingNeedsWorkForm, FundingNeedsWorkMessage),
            (GrantApplication, 'approve', GrantApplicationApproveForm, GrantApplicationApprovedMessage),
            (GrantApplication, 'reject', GrantApplicationRejectedForm, GrantApplicationRejectedMessage),
            (GrantApplication, 'request_changes', GrantApplicationNeedsWorkForm, GrantApplicationNeedsWorkMessage),
        ]

        for model, transition_name, form_class, message_class in cases:
            with self.subTest(model=model.__name__, transition=transition_name):
                transition = model._state_machines['states'].transitions[transition_name]
                self.assertEqual(transition.form, form_class)
                self.assertTrue(_form_has_custom_message_field(form_class))
                self.assertIn(message_class, _notification_messages_for_transition(model, transition))

    def test_known_custom_message_gaps(self):
        accept_transition = DateRegistration._state_machines['states'].transitions['accept']
        reject_transition = DateRegistration._state_machines['states'].transitions['reject']

        self.assertTrue(_form_has_custom_message_field(RegistrationAcceptForm))
        self.assertTrue(_form_has_custom_message_field(RegistrationRejectForm))
        self.assertIsNone(accept_transition.form)
        self.assertIsNone(reject_transition.form)
        self.assertIn(
            UserRegistrationAcceptedNotification,
            _notification_messages_for_transition(DateRegistration, accept_transition),
        )
        self.assertIn(
            UserRegistrationRejectedNotification,
            _notification_messages_for_transition(DateRegistration, reject_transition),
        )


class CustomMessageIntegrationTestCase(TriggerTestCase):
    factory = DeedFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(is_staff=True)
        image = ImageFactory()
        self.image = image
        self.deed_defaults = {
            'initiative': InitiativeFactory.create(status='approved'),
            'owner': self.owner,
            'title': ACTIVITY_TITLE,
            'image': image,
            'start': date.today() + timedelta(days=10),
            'end': date.today() + timedelta(days=20),
        }
        self.date_activity_defaults = {
            'initiative': InitiativeFactory.create(status='approved'),
            'owner': self.owner,
            'title': ACTIVITY_TITLE,
            'image': image,
            'slots': [],
        }
        self.defaults = dict(self.deed_defaults)

    def _send_transition_mail(self, transition_name, submit_first=False):
        if submit_first:
            self.defaults['initiative'] = None
        self.create()
        if submit_first:
            self.model.states.submit(save=True)
        getattr(self.model.states, transition_name)()
        mail.outbox = []
        self.model.execute_triggers(message=CUSTOM_MESSAGE, send_messages=True)
        self.model.save()
        return [message for message in mail.outbox if self.owner.email in message.to]

    def test_deed_reject_custom_message_in_mail(self):
        messages = self._send_transition_mail('reject')
        self.assertEqual(len(messages), 1)
        self.assertIn(CUSTOM_MESSAGE, messages[0].body)
        self.assertNotIn('Unfortunately your activity', messages[0].body)

    def test_deed_reject_rich_text_custom_message_in_mail(self):
        self.create()
        getattr(self.model.states, 'reject')()
        mail.outbox = []
        self.model.execute_triggers(message=CUSTOM_MESSAGE_HTML, send_messages=True)
        self.model.save()
        messages = [message for message in mail.outbox if self.owner.email in message.to]
        self.assertEqual(len(messages), 1)
        self.assertIn('update', messages[0].body)
        self.assertIn('<strong>update</strong>', messages[0].alternatives[0][0])
        self.assertNotIn('Unfortunately your activity', messages[0].body)

    def test_deed_approve_custom_message_in_mail(self):
        self.defaults['initiative'] = None
        messages = self._send_transition_mail('approve', submit_first=True)
        self.assertTrue(messages)
        self.assertTrue(any(CUSTOM_MESSAGE in message.body for message in messages))
        self.assertFalse(any('Good news, your activity' in message.body for message in messages))

    def test_grant_reject_custom_message_in_mail(self):
        self.factory = GrantApplicationFactory
        self.defaults = {
            'initiative': None,
            'owner': self.owner,
            'title': ACTIVITY_TITLE,
        }
        messages = self._send_transition_mail('reject', submit_first=True)
        self.assertEqual(len(messages), 1)
        self.assertIn(CUSTOM_MESSAGE, messages[0].body)
        self.assertNotIn('Unfortunately your grant application', messages[0].body)

    def test_grant_needs_work_custom_message_in_mail(self):
        self.factory = GrantApplicationFactory
        self.defaults = {
            'initiative': None,
            'owner': self.owner,
            'title': ACTIVITY_TITLE,
        }
        messages = self._send_transition_mail('request_changes', submit_first=True)
        self.assertEqual(len(messages), 1)
        self.assertIn(CUSTOM_MESSAGE, messages[0].body)

    def test_grant_approve_custom_message_in_mail(self):
        fund = GrantFundFactory.create()
        GrantDepositFactory.create(fund=fund, amount=Money(1500, 'EUR'))
        self.factory = GrantApplicationFactory
        self.defaults = {
            'initiative': None,
            'owner': self.owner,
            'title': ACTIVITY_TITLE,
            'target': Money(500, 'EUR'),
        }
        self.create()
        self.model.states.submit(save=True)

        transition = self.model.states.transitions['approve']
        form = GrantApplicationApproveForm(
            data={
                'fund': str(fund.pk),
                'amount_0': '500',
                'amount_1': 'EUR',
                'custom_message': CUSTOM_MESSAGE,
                'send_messages': True,
            },
            instance=self.model,
            transition=transition,
        )
        self.assertTrue(form.is_valid(), form.errors)

        self.model.states.approve()
        mail.outbox = []
        form.save()
        custom_message = getattr(transition, 'custom_message', None)
        self.model.execute_triggers(send_messages=True, message=custom_message)
        self.model.save()
        messages = [message for message in mail.outbox if self.owner.email in message.to]
        self.assertEqual(len(messages), 1)
        self.assertIn(CUSTOM_MESSAGE, messages[0].body)
        self.assertNotIn('Good news, your grant application', messages[0].body)

    def test_collect_reject_custom_message_in_mail(self):
        self.factory = CollectActivityFactory
        self.defaults = dict(self.deed_defaults)
        messages = self._send_transition_mail('reject')
        self.assertEqual(len(messages), 1)
        self.assertIn(CUSTOM_MESSAGE, messages[0].body)

    def test_date_activity_reject_custom_message_in_mail(self):
        self.factory = DateActivityFactory
        self.defaults = dict(self.date_activity_defaults)
        messages = self._send_transition_mail('reject')
        self.assertEqual(len(messages), 1)
        self.assertIn(CUSTOM_MESSAGE, messages[0].body)

    def test_deed_request_changes_custom_message_in_mail(self):
        self.factory = DeedFactory
        self.defaults = dict(self.deed_defaults)
        self.defaults['initiative'] = None
        self.create()
        self.model.states.submit(save=True)
        self.model.states.request_changes()
        mail.outbox = []
        self.model.execute_triggers(message=CUSTOM_MESSAGE, send_messages=True)
        self.model.save()
        messages = [message for message in mail.outbox if self.owner.email in message.to]
        self.assertEqual(len(messages), 1)
        self.assertIn(CUSTOM_MESSAGE, messages[0].body)
        self.assertNotIn('has been reviewed and needs work', messages[0].body)
