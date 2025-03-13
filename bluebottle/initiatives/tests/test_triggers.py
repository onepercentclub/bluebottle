from django.core import mail
from bluebottle.deeds.tests.factories import DeedFactory

from bluebottle.deeds.states import DeedStateMachine
from bluebottle.funding.states import FundingStateMachine
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.funding_stripe.tests.factories import (
    ExternalAccountFactory,
    StripePayoutAccountFactory,
)
from bluebottle.initiatives.messages import InitiativeSubmittedStaffMessage
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, TriggerTestCase


class InitiativeOldTriggerTests(BluebottleTestCase):

    def setUp(self):
        super(InitiativeOldTriggerTests, self).setUp()
        self.user = BlueBottleUserFactory.create(first_name='Bart', last_name='Lacroix')
        self.initiative = InitiativeFactory.create(
            has_organization=False,
            owner=self.user,
            organization=None
        )

    def test_set_reviewer(self):
        mail.outbox = []
        self.initiative.reviewer = BlueBottleUserFactory.create(email='reviewer@goodup.com')
        self.initiative.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('You are assigned as reviewer' in mail.outbox[0].body)
        self.assertEqual(['reviewer@goodup.com'], mail.outbox[0].to)


class InitiativeTriggerTestCase(TriggerTestCase):
    factory = InitiativeFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True
        )
        self.defaults = {
            'owner': self.owner,
        }
        super().setUp()

    def test_submit(self):
        self.create()
        self.model.states.submit()
        with self.execute():
            self.assertNotificationEffect(InitiativeSubmittedStaffMessage)
        self.model.save()
        self.assertEqual(self.model.published, None)
        self.assertStatus(self.model, 'submitted')

    def test_publish(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_reviewing = False
        initiative_settings.save()
        self.create()
        self.model.states.publish(save=True)
        self.assertNotEqual(self.model.published, None)
        self.assertStatus(self.model, 'approved')

    def test_auto_submit_activity(self):
        self.create()
        activity = DeedFactory.create(initiative=self.model)

        self.model.states.submit()
        with self.execute():
            self.assertTransitionEffect(DeedStateMachine.auto_submit, activity)

    def test_auto_submit_funding_activity(self):
        self.create()
        activity = FundingFactory.create(initiative=self.model)

        self.model.states.submit()
        with self.execute():
            self.assertNoTransitionEffect(FundingStateMachine.auto_submit, activity)

    def test_auto_submit_funding_activity_complete(self):
        self.create()
        activity = FundingFactory.create(
            initiative=self.model,
            bank_account=ExternalAccountFactory.create(
                status="verified",
                connect_account=StripePayoutAccountFactory.create(
                    status="verified", account_id='test-account-id'
                ),
            ),
        )

        self.model.states.submit()
        with self.execute():
            self.assertNoTransitionEffect(FundingStateMachine.auto_submit, activity)
