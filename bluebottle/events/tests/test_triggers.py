from djmoney.money import Money

from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, BankAccountFactory, \
    PlainPayoutAccountFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.events.models import Event, Webhook
from bluebottle.updates.models import Update


class EventTriggerTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = PlainPayoutAccountFactory.create(status="verified")
        bank_account = BankAccountFactory.create(
            connect_account=payout_account, status="verified"
        )
        self.funding.bank_account = bank_account
        self.funding.states.submit(save=True)

    def test_approve_funding(self):
        self.funding.states.approve(save=True)

        event = Event.objects.get(type='funding.approved')

        self.assertEqual(event.content_object, self.funding)

        update = Update.objects.get()
        self.assertEqual(update.author, self.funding.owner)
        self.assertEqual(update.event, event)


class WebhookTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.activity = DeedFactory.create(initiative=self.initiative)
        self.hook = Webhook.objects.create(url="http://localhost:5000/hook")

    def test_webhook(self):
        self.activity.states.publish(save=True)
        __import__('ipdb').set_trace()
