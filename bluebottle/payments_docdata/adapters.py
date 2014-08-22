import logging
from bluebottle.payments.adapters import BasePaymentAdapter
from django.utils.http import urlencode
import gateway
from bluebottle.payments_logger.adapters import PaymentLogAdapter
from django.conf import settings
from .models import DocdataPayment
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)
payment_docdata_logger = logging.getLogger('payment.docdata')


class DocdataPaymentAdapter(BasePaymentAdapter):

    MODEL_CLASS = DocdataPayment

    def __init__(self, *args, **kwargs):
        super(DocdataPaymentAdapter, self).__init__(*args, **kwargs)
        self.payment_logger = PaymentLogAdapter(payment_docdata_logger)

    def create_payment(self):
        payment = self.MODEL_CLASS(order_payment=self.order_payment, **self.order_payment.integration_data)
        payment.total_gross_amount = self.order_payment.amount

        # Make sure that Payment has an ID
        payment.save()

        testing_mode = settings.DOCDATA_SETTINGS['testing_mode']

        merchant = gateway.Merchant(name=settings.DOCDATA_MERCHANT_NAME, password=settings.DOCDATA_MERCHANT_PASSWORD)

        amount = gateway.Amount(value=self.order_payment.amount, currency='EUR')
        user = self.get_user_data()

        name = gateway.Name(
            first=user['first_name'],
            last=user['last_name']
        )

        shopper = gateway.Shopper(
            id=user['id'],
            name=name,
            email=user['email'],
            language='en',
            gender="U",
            date_of_birth=None,
            phone_number=None,
            mobile_phone_number=None,
            ipAddress=None)

        address = gateway.Address(
            street=u'Unknown',
            house_number='1',
            house_number_addition=u'',
            postal_code='Unknown',
            city=u'Unknown',
            state=u'',
            country_code='NL',
        )

        bill_to = gateway.Destination(name=name, address=address)

        client = gateway.DocdataClient(testing_mode)

        response = client.create(
            merchant=merchant,
            payment_id=payment.id,
            total_gross_amount=amount,
            shopper=shopper,
            bill_to=bill_to,
            description=_("Bluebottle donation"),
            receiptText=_("Bluebottle donation"),
            includeCosts=False,
            profile=settings.DOCDATA_SETTINGS['profile'],
            days_to_pay=settings.DOCDATA_SETTINGS['days_to_pay'],
            )

        payment.payment_cluster_key = response['order_key']
        payment.payment_cluster_id = response['order_id']
        payment.save()

        return payment

    def get_authorization_action(self):

        testing_mode = settings.DOCDATA_SETTINGS['testing_mode']

        client = gateway.DocdataClient(testing_mode)

        return_url = 'http://localhost:8000'
        client_language = 'en'

        integration_data = self.order_payment.integration_data

        url = client.get_payment_menu_url(
            order_key=self.payment.payment_cluster_key,
            order_id=self.order_payment.order_id,
            return_url=return_url,
            client_language=client_language,
        )

        default_act = False
        if self.payment.ideal_issuer_id:
            default_act = True

        params = {
             'default_pm': self.payment.default_pm,
             'ideal_issuer_id': self.payment.ideal_issuer_id,
             'default_act': default_act
        }
        url += '&' + urlencode(params)
        return {'type': 'redirect', 'method': 'get', 'url': url}

