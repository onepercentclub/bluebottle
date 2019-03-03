from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.urls import reverse

from bluebottle.donations.admin import DonationAdmin
from bluebottle.donations.models import Donation
from bluebottle.members.tests.test_admin import MockUser
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory, MockPaymentFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class DonationAdminTest(BluebottleAdminTestCase):
    def setUp(self):
        super(DonationAdminTest, self).setUp()
        self.some_user = BlueBottleUserFactory.create()
        self.order = OrderFactory.create(user=self.some_user)
        self.order_payment = OrderPaymentFactory.create(order=self.order)
        self.payment = MockPaymentFactory.create(order_payment=self.order_payment)
        self.donation = DonationFactory.create(order=self.order)
        self.donation_admin = DonationAdmin(Donation, AdminSite())
        self.client.force_login(self.superuser)
        self.donation_url = reverse('admin:donations_donation_change', args=(self.donation.id, ))
        self.donation_list_url = reverse('admin:donations_donation_changelist')
        self.request = RequestFactory().get('/')
        self.request.user = MockUser()

    def test_donation_list_admin(self):
        response = self.client.get(self.donation_list_url)
        self.assertEqual(response.status_code, 200)

    def test_donation_admin(self):
        response = self.client.get(self.donation_url)
        self.assertEqual(response.status_code, 200)

    def test_donation_admin_full_name(self):
        user = self.donation_admin.user(self.donation)
        self.assertEqual(user, self.some_user)

        full_name = self.donation_admin.user_full_name(self.donation)
        self.assertEqual(full_name, self.some_user.full_name)

        self.order.user = None
        self.order.save()
        full_name = self.donation_admin.user_full_name(self.donation)
        self.assertEqual(full_name, '-guest-')

        self.donation.anonymous = True
        self.donation.save()
        full_name = self.donation_admin.user_full_name(self.donation)
        self.assertEqual(full_name, '-anonymous-')

    def test_donation_admin_payment(self):
        payment_method = self.donation_admin.related_payment_method(self.donation)
        self.assertEqual(payment_method, 'mock')
