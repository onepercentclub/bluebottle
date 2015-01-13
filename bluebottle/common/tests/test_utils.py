from django.core.urlresolvers import reverse

from mock import patch

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.payments.views import PaymentMethodList
from bluebottle.utils.utils import get_country_by_ip, InvalidIpError
from bluebottle.payments.services import get_payment_methods


class TestUtilsTestCase(BluebottleTestCase):
    def test_no_ip(self):
    	self.assertEqual(get_country_by_ip(), None)

    def test_invalid_ip(self):
    	with self.assertRaises(InvalidIpError):
    		get_country_by_ip("123abc")

    def test_valid_ip(self):
    	self.assertEqual(get_country_by_ip("213.127.165.114"), "Netherlands")

    def test_load_all_payment_methods(self):
    	methods = get_payment_methods(country="all")
    	self.assertEqual(len(methods), 3)

    def test_load_netherlands_payment_methods(self):
    	methods = get_payment_methods(country="Netherlands")
    	self.assertEqual(len(methods), 2)

    def test_load_non_netherlands_payment_methods(self):
    	methods = get_payment_methods(country="Belgium")
    	self.assertEqual(len(methods), 2)
