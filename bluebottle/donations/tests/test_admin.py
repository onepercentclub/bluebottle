from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from bluebottle.donations.admin import DonationAdmin
from bluebottle.donations.models import Donation
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class DonationAdminTest(BluebottleAdminTestCase):
    def setUp(self):
        super(DonationAdminTest, self).setUp()
        self.donation = DonationFactory.create()
        self.donation_admin = DonationAdmin(Donation, AdminSite())
        self.client.force_login(self.superuser)
        self.donation_url = reverse('admin:donations_donation_change', args=(self.donation.id, ))
        self.donation_list_url = reverse('admin:donations_donation_changelist')

    def test_donation_list_admin(self):
        response = self.client.get(self.donation_list_url)
        self.assertEqual(response.status_code, 200)

    def test_donation_admin(self):
        response = self.client.get(self.donation_url)
        self.assertEqual(response.status_code, 200)
