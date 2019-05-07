import os

from django.test import override_settings
from mock import patch

from bluebottle.utils.utils import json2obj
from django.contrib.admin import AdminSite

from bluebottle.payouts.models import StripePayoutAccount
from django.contrib.auth.models import Permission, Group
from django.core.urlresolvers import reverse

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.payouts import PlainPayoutAccountFactory, StripePayoutAccountFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.payouts.admin.stripe import StripePayoutAccountAdmin


MERCHANT_ACCOUNTS = [
    {
        'merchant': 'stripe',
        'currency': 'EUR',
        'secret_key': 'sk_test_secret_key',
        'webhook_secret': 'whsec_test_webhook_secret',
        'webhook_secret_connect': 'whsec_test_webhook_secret_connect',
    }
]

PROJECT_PAYOUT_FEES = {
    'beneath_threshold': 1,
    'fully_funded': 0.05,
    'not_fully_funded': 0.0725
}


@override_settings(MERCHANT_ACCOUNTS=MERCHANT_ACCOUNTS)
class StripePayoutTestAdmin(BluebottleAdminTestCase):
    def setUp(self):
        super(StripePayoutTestAdmin, self).setUp()
        self.payout = StripePayoutAccountFactory.create(

        )
        self.site = AdminSite()
        self.admin = StripePayoutAccountAdmin(StripePayoutAccount, self.site)

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    def test_stripe_details(self, stripe_retrieve):
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified.json').read()
        )
        details = self.admin.details(self.payout)
        self.assertEqual(details,
                         '<b>account number</b>: *************1234<br/>'
                         u'<b>account holder name</b>: M\xe5lle Eppie<br/>'
                         '<b>last name</b>: Eppie<br/>'
                         '<b>country</b>: NL<br/>'
                         '<b>bank country</b>: DE<br/><b>currency</b>: eur<br/>'
                         u'<b>first name</b>: M\xe5lle')

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    def test_stripe_details_xss(self, stripe_retrieve):
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified_xss.json').read()
        )
        details = self.admin.details(self.payout)
        self.assertEqual(
            details,
            '<b>account number</b>: *************1234<br/>'
            u'<b>account holder name</b>: M\xe5lle Eppie&lt;script&gt;alert(&#39;test&#39;)&lt;/script&gt;<br/>'
            '<b>last name</b>: Eppie<br/>'
            '<b>country</b>: NL<br/>'
            '<b>bank country</b>: DE<br/><b>currency</b>: eur<br/>'
            u'<b>first name</b>: M\xe5lle'
        )

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    def test_stripe_cached_details(self, stripe_retrieve):
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_unverified.json').read()
        )
        details = self.admin.details(self.payout)
        self.assertEqual(details,
                         '<b>account number</b>: *************1234<br/>'
                         '<b>account holder name</b>: Dolle Mina<br/>'
                         '<b>last name</b>: Mina<br/>'
                         '<b>country</b>: NL<br/>'
                         '<b>bank country</b>: DE<br/><b>currency</b>: eur<br/>'
                         '<b>first name</b>: Dolle')

        # Change Stripe response
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified.json').read()
        )

        # Should be cached
        details = self.admin.details(self.payout)
        self.assertEqual(details,
                         '<b>account number</b>: *************1234<br/>'
                         '<b>account holder name</b>: Dolle Mina<br/>'
                         '<b>last name</b>: Mina<br/>'
                         '<b>country</b>: NL<br/>'
                         '<b>bank country</b>: DE<br/><b>currency</b>: eur<br/>'
                         '<b>first name</b>: Dolle')

        # Check status should update it
        self.payout.check_status()
        details = self.admin.details(self.payout)
        self.assertEqual(details,
                         '<b>account number</b>: *************1234<br/>'
                         u'<b>account holder name</b>: M\xe5lle Eppie<br/>'
                         '<b>last name</b>: Eppie<br/>'
                         '<b>country</b>: NL<br/>'
                         '<b>bank country</b>: DE<br/><b>currency</b>: eur<br/>'
                         u'<b>first name</b>: M\xe5lle')


class PayoutAccountAdminTestCase(BluebottleAdminTestCase):

    def setUp(self):
        self.user = BlueBottleUserFactory.create(is_staff=True)
        self.account = PlainPayoutAccountFactory.create()
        self.project = ProjectFactory.create(payout_account=self.account)
        self.payout_url = reverse('admin:payouts_payoutaccount_change', args=(self.account.id,))
        self.payout_reviewed_url = reverse('admin:plain-payout-account-reviewed', args=(self.account.id,))

    def test_permissions_denied(self):
        self.client.force_login(self.user)
        response = self.client.get(self.payout_url)
        self.assertEqual(response.status_code, 403)

    def test_permissions_granted_user(self):
        # Check user has permission when added specific permission
        self.user.user_permissions.add(
            Permission.objects.get(codename='change_plainpayoutaccount')
        )
        self.client.force_login(self.user)
        response = self.client.get(self.payout_url)
        self.assertEqual(response.status_code, 200)

    def test_permissions_granted_staff(self):
        # Check that user has permission if added to Staff group
        self.user.groups.add(Group.objects.get(name='Staff'))
        self.client.force_login(self.user)
        response = self.client.get(self.payout_url)
        self.assertEqual(response.status_code, 200)

    def test_permission_set_reviewed(self):
        self.assertEqual(self.account.reviewed, False)
        self.user.groups.add(Group.objects.get(name='Staff'))
        self.client.force_login(self.user)
        response = self.client.get(self.payout_reviewed_url)
        self.assertRedirects(response, self.payout_url)
        self.account.refresh_from_db()
        self.assertEqual(self.account.reviewed, True)
