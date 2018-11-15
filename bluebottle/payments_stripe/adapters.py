import logging

from bluebottle.clients import properties
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments_stripe.models import StripePayment
from bluebottle.utils.utils import get_client_ip

logger = logging.getLogger(__name__)


class StripePaymentAdapter(BasePaymentAdapter):

    def __init__(self, *args, **kwargs):
        self.live_mode = getattr(properties, 'LIVE_PAYMENTS_ENABLED', False)
        super(StripePaymentAdapter, self).__init__(*args, **kwargs)

    def get_user_data(self):
        user = self.order_payment.order.user
        ip_address = get_client_ip()

        if user:
            user_data = {
                'id': user.id,
                'first_name': user.first_name or 'Unknown',
                'last_name': user.last_name or 'Unknown',
                'email': user.email,
                'ip_address': ip_address,
            }
        else:
            user_data = {
                'id': 1,
                'first_name': 'Nomen',
                'last_name': 'Nescio',
                'email': properties.CONTACT_EMAIL,
                'ip_address': ip_address
            }

        default_country_code = getattr(properties, 'DEFAULT_COUNTRY_CODE')

        if user and hasattr(user, 'address'):
            street = user.address.line1.split(' ')
            if street[-1] and any(char.isdigit() for char in street[-1]):
                user_data['house_number'] = street.pop(-1)
                if len(street):
                    user_data['street'] = ' '.join(street)
                else:
                    user_data['street'] = 'Unknown'
            else:
                user_data['house_number'] = 'Unknown'
                if user.address.line1:
                    user_data['street'] = user.address.line1
                else:
                    user_data['street'] = 'Unknown'

            if user.address.postal_code:
                user_data['postal_code'] = user.address.postal_code
            else:
                user_data['postal_code'] = 'Unknown'
            if user.address.city:
                user_data['city'] = user.address.city
            else:
                user_data['city'] = 'Unknown'
            if user.address.country and hasattr(user.address.country,
                                                'alpha2_code'):
                user_data['country'] = user.address.country.alpha2_code
            else:
                user_data['country'] = default_country_code
        else:
            user_data['postal_code'] = 'Unknown'
            user_data['street'] = 'Unknown'
            user_data['city'] = 'Unknown'
            user_data['country'] = default_country_code
            user_data['house_number'] = 'Unknown'

        if not user_data['country']:
            user_data['country'] = default_country_code

        user_data['company'] = ''
        user_data['kvk_number'] = ''
        user_data['vat_number'] = ''
        user_data['house_number_addition'] = ''
        user_data['state'] = ''

        return user_data

    def create_payment(self):
        payment = StripePayment(order_payment=self.order_payment, **self.order_payment.card_data)
        payment.save()

        return payment

    def check_payment_status(self):
        pass

    def refund_payment(self):
        pass

    def get_authorization_action(self):
        return {}
