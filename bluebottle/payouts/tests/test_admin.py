from django.contrib.auth.models import Permission, Group
from django.core.urlresolvers import reverse

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.payouts import PlainPayoutAccountFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleAdminTestCase


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
