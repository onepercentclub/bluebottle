from mock import patch
import os

from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.factory_models.payouts import StripePayoutAccountFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import json2obj
from bluebottle.test.factory_models.projects import ProjectFactory

MERCHANT_ACCOUNTS = [
    {
        'merchant': 'stripe',
        'currency': 'EUR',
        'secret_key': 'sk_test_secret_key',
        'webhook_secret': 'whsec_test_webhook_secret'
    }
]


@override_settings(MERCHANT_ACCOUNTS=MERCHANT_ACCOUNTS)
class StripePayoutAccountTestCase(BluebottleTestCase):

    def setUp(self):
        super(StripePayoutAccountTestCase, self).setUp()
        self.init_projects()
        self.payout_account = StripePayoutAccountFactory.create(account_id='acct_0000000123')

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    def test_check_status(self, stripe_retrieve):
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified.json').read()
        )
        self.assertEquals(self.payout_account.reviewed, False)
        self.payout_account.check_status()
        self.payout_account.refresh_from_db()
        self.assertEquals(self.payout_account.reviewed, True)

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    def test_check_status_unverified(self, stripe_retrieve):
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_unverified.json').read()
        )
        self.assertEquals(self.payout_account.reviewed, False)
        self.payout_account.check_status()
        self.payout_account.refresh_from_db()
        self.assertEquals(self.payout_account.reviewed, False)


class PayoutBaseTestCase(BluebottleTestCase):
    """ Base test case for Payouts. """

    def setUp(self):
        super(PayoutBaseTestCase, self).setUp()

        self.init_projects()

        # Set up a project ready for payout
        self.organization = OrganizationFactory.create()
        self.organization.save()
        self.project = ProjectFactory.create(organization=self.organization, amount_asked=50)
        self.project_incomplete = ProjectFactory.create(organization=self.organization, amount_asked=100)

        # Update phase to campaign.
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

        self.project_incomplete.status = ProjectPhase.objects.get(slug='campaign')
        self.project_incomplete.save()

        self.order = OrderFactory.create()

        self.donation = DonationFactory.create(
            project=self.project,
            order=self.order,
            amount=60
        )
        self.donation.save()

        self.donation2 = DonationFactory.create(
            project=self.project_incomplete,
            order=self.order,
            amount=60
        )
        self.donation2.save()
