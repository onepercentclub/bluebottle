# coding=utf-8
from bluebottle.payments.adapters import AbstractPaymentAdapter
from bluebottle.payments.models import Payment
from django.conf import settings
from .models import MolliePayment
import Mollie


class MolliePaymentAdapter(AbstractPaymentAdapter):

    @staticmethod
    def create_payment(order_payment, integration_data=None):
        payment = MolliePayment(**integration_data)
        payment.order_payment = order_payment
        payment.amount = order_payment.amount
        payment.redirect_url = 'http://localhost:8000/en/#!/orders/{0}/success'.format(order_payment.order.id)
        if order_payment.payment_method == 'mollieIdeal':
            payment.method = Mollie.API.Object.Method.IDEAL
        if order_payment.payment_method == 'mollieCreditcard':
            payment.method = Mollie.API.Object.Method.CREDITCARD
        payment.save()
        return payment

    @staticmethod
    def get_authorization_action(order_payment):

        # FIXME Improve and make this bullet proof
        payment = MolliePayment.objects.filter(order_payment=order_payment).all()[0]

        mollie = Mollie.API.Client()
        mollie.setApiKey(settings.MOLLIE_API_KEY)

        # Generate Mollie Payment
        mollie_payment = mollie.payments.create({
            'amount': str(payment.amount),
            'method': payment.method,
            # 'issuer': 'ideal_TESTNL99',
            'description': 'One Percent Club Donation',
            'redirectUrl': payment.redirect_url
        })

        """
        Mollie response
        {u'status': u'open',
        u'description': u'One Percent Club Donation',
        u'links': {
            u'redirectUrl': u'http://localhost:8000/en/#!/orders/2',
            u'paymentUrl': u'https://www.mollie.nl/payscreen/pay/SuFCDjGgRa'},
        u'createdDatetime': u'2014-08-17T07:05:51.0Z',
        u'expiryPeriod': u'PT15M',
        u'id': u'tr_SuFCDjGgRa',
        u'amount': u'50.00',
        u'mode': u'test',
        u'metadata': None,
        u'method': None,
        u'details': None}
        """

        payment.payment_url = mollie_payment['links']['paymentUrl']
        payment.status = mollie_payment['status']
        payment.save()

        return {'type': 'redirect', 'url': payment.payment_url, 'method': 'get'}


    @staticmethod
    def _check_payment_status(payment):
        # FIXME: Check the status at PSP
        pass