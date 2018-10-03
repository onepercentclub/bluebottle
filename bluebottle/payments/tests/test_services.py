from django.test.utils import override_settings

from bluebottle.payments.services import get_payment_methods
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


# test handler which grants access if the member is staff
def method_access_handler(member, *args, **kwargs):
    return member.is_staff


@override_settings(SKIP_IP_LOOKUP=False)
@override_settings(PAYMENT_METHODS=(
    {
        'provider': 'docdata',
        'id': 'docdata-creditcard',
        'profile': 'creditcard',
        'name': 'CreditCard',
    },
    {
        'provider': 'pledge',
        'id': 'pledge-standard',
        'name': 'Pledge',
        'profile': 'standard',
        'method_access_handler': 'bluebottle.payments.tests.test_services.method_access_handler'
    }
))
class PaymentMethodHandlerTestCase(BluebottleTestCase):
    def test_pledge_payment_methods(self):
        user = BlueBottleUserFactory.create(is_staff=False)
        staff_user = BlueBottleUserFactory.create(is_staff=True)

        methods = get_payment_methods(country="nl", user=user)
        self.assertEqual(len(methods), 1)

        methods = get_payment_methods(country="nl", user=staff_user)
        self.assertEqual(len(methods), 2)

    @override_settings(PAYMENT_METHODS=(
        {
            'provider': 'pledge',
            'id': 'pledge-standard',
            'name': 'Pledge',
            'profile': 'standard',
            'method_access_handler': 'bluebottle.foo.bar'
        },
    ))
    def test_invalid_method_access_handler(self):
        user = BlueBottleUserFactory.create()

        with self.assertRaises(Exception):
            get_payment_methods(country="nl", user=user)


class PaymentMethodTestCase(BluebottleTestCase):
    def test_load_all_payment_methods(self):
        methods = get_payment_methods(country=None)
        self.assertEqual(len(methods), 3)

    def test_load_netherlands_payment_methods(self):
        methods = get_payment_methods(country="Netherlands")
        self.assertEqual(len(methods), 2)

    def test_load_non_netherlands_payment_methods(self):
        methods = get_payment_methods(country="Belgium")
        self.assertEqual(len(methods), 2)

    def test_load_euro_payment_methods(self):
        methods = get_payment_methods(currency="EUR")
        self.assertEqual(len(methods), 2)

        for method in methods:
            self.assertTrue('EUR' in method['currencies'])

    def test_load_non_dutch_euro_payment_methods(self):
        methods = get_payment_methods(currency="EUR", country='Belgium')
        self.assertEqual(len(methods), 1)

        for method in methods:
            self.assertTrue('EUR' in method['currencies'])
