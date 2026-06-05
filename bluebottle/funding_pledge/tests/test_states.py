from bluebottle.funding.tests.factories import DonorFactory, FundingFactory
from bluebottle.funding_pledge.tests.factories import (
    PledgePaymentFactory,
    PledgePaymentProviderFactory,
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class PledgePaymentStateMachineTestCase(BluebottleTestCase):
    def setUp(self):
        super(PledgePaymentStateMachineTestCase, self).setUp()
        self.init_projects()
        PledgePaymentProviderFactory.create()
        self.user = BlueBottleUserFactory.create()
        initiative = InitiativeFactory.create()
        initiative.states.submit()
        initiative.states.approve(save=True)
        self.funding = FundingFactory.create(initiative=initiative)
        self.donation = DonorFactory.create(activity=self.funding, user=self.user)
        self.payment = PledgePaymentFactory.create(donation=self.donation)

    def test_request_refund_transition_moves_to_refunded(self):
        self.payment.states.request_refund(save=True)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'refunded')
