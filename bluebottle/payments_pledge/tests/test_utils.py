from django.test.utils import override_settings

from bluebottle.payments.services import get_payment_methods
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


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
        'method_access_handler': 'bluebottle.payments_pledge.utils.method_access_handler'
    }
))
class PaymentMethodHandlerTestCase(BluebottleTestCase):
    def test_pledge_payment_methods(self):
        user = BlueBottleUserFactory.create(can_pledge=False)
        staff_user = BlueBottleUserFactory.create(can_pledge=True)

        methods = get_payment_methods(country="nl", user=user)
        self.assertEqual(len(methods), 1)

        methods = get_payment_methods(country="nl", user=staff_user)
        self.assertEqual(len(methods), 2)
