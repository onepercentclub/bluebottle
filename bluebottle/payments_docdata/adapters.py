# coding=utf-8
import logging
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments_docdata.exceptions import MerchantTransactionIdNotUniqueException
from django.utils.http import urlencode
import gateway
from interface import DocdataInterface
from django.conf import settings
from .models import DocdataPayment

logger = logging.getLogger(__name__)


class DocdataPaymentAdapter(BasePaymentAdapter):

    MODEL_CLASS = DocdataPayment

    def create_payment(self):
        payment = self.MODEL_CLASS(order_payment=self.order_payment, **self.order_payment.integration_data)
        payment.total_gross_amount = self.order_payment.amount

        testing_mode = True

        merchant = gateway.Merchant(name=settings.DOCDATA_MERCHANT_NAME, password=settings.DOCDATA_MERCHANT_PASSWORD)

        amount = gateway.Amount(value=self.order_payment.amount, currency='EUR')
        user = self.order_payment.order.user

        name = gateway.Name(
            first=u'Henkie',
            last=u'Henk'
        )

        shopper = gateway.Shopper(
            id=user.id,
            name=name,
            email=user.email,
            language='en',
            gender="U",
            date_of_birth=None,
            phone_number=None,
            mobile_phone_number=None,
            ipAddress=None)

        address = gateway.Address(
            street=u'Henkdijk',
            house_number='1',
            house_number_addition=u'',
            postal_code='u1234HK',
            city=u'Henkendam',
            state=u'',
            country_code='NL',
        )

        bill_to = gateway.Destination(name=name, address=address)

        client = gateway.DocdataClient(testing_mode)

        merchant_order_id = "{0}-{1}".format(self.order_payment.id, 'a')

        response = client.create(
            merchant=merchant,
            payment_id=self.order_payment.id,
            total_gross_amount=amount,
            shopper=shopper,
            bill_to=bill_to,
            description="Bluebottle donation",
            receiptText="Bluebottle donation",
            includeCosts=False,
            profile='webmenu',
            days_to_pay=5,
            )

        payment.merchant_order_id = merchant_order_id
        payment.payment_cluster_key = response['order_key']
        payment.payment_cluster_id = response['order_id']
        payment.save()

        return payment

    def get_authorization_action(self):

        testing_mode = True

        client = gateway.DocdataClient(testing_mode)

        return_url = 'http://localhost:8000/payments_docdata/payment/'
        client_language = 'en'

        integration_data = self.order_payment.integration_data

        url = client.get_payment_menu_url(
            order_key=self.payment.payment_cluster_key,
            return_url=return_url,
            client_language=client_language,
        )

        params = {
            'default_pm': getattr(integration_data, 'default_pm', None),
            'ideal_issuer_id': getattr(integration_data, 'ideal_issuer_id', None),
            'default_act': 'true'
        }

        url += '&' + urlencode(params)
        return {'type': 'redirect', 'method': 'get', 'url': url}

