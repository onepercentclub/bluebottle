# coding=utf-8
import logging

import requests
from django.db import connection

from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments.exception import PaymentException
from .models import FlutterwavePayment

logger = logging.getLogger(__name__)


SUCCESS_RESPONSECODES = ['0', '00']


class FlutterwaveCreditcardPaymentAdapter(BasePaymentAdapter):

    verify_url = "https://api.ravepay.co/flwv3-pug/getpaidx/api/v2/verify"
    card_data = {}

    def create_payment(self):
        self.card_data = self.order_payment.card_data

        if 'tx_ref' not in self.card_data:
            raise PaymentException('TxRef is required')

        payment = FlutterwavePayment(
            order_payment=self.order_payment,
            transaction_reference=self.card_data['tx_ref']
        )
        payment.amount = str(self.order_payment.amount.amount)
        payment.currency = str(self.order_payment.amount.currency)
        payment.customer_id = str(self.order_payment.user or 1)
        payment.narration = "Donation {0}".format(self.order_payment.id)
        payment.response_url = '{0}/payments_flutterwave/payment_response/{1}'.format(
            connection.tenant.domain_url,
            self.order_payment.id)
        tenant = connection.tenant
        payment.site_name = str(tenant.domain_url)
        try:
            payment.cust_id = self.order_payment.user.id
            payment.cust_name = unicode(self.order_payment.user.full_name)
        except AttributeError:
            # Anonymous order
            pass
        payment.save()
        return payment

    def get_authorization_action(self):
        if not {'tx_ref'}.issubset(self.card_data):
            raise PaymentException('TxRef is required')
        self.check_payment_status()
        if self.payment.status in ['settled', 'pending']:
            return {'type': 'success'}
        raise PaymentException('Error starting payment')

    def post(self, url, data):
        response = requests.post(url, json=data)
        if response.status_code != 200:
            raise PaymentException(response.content)
        return response.json()

    def check_payment_status(self):
        data = {
            'txref': self.payment.transaction_reference,
            'SECKEY': self.credentials['sec_key']
        }
        data = self.post(self.verify_url, data)
        self.payment.response = data

        if data['data']['status'] == 'success':
            self.order_payment.set_authorization_action({'type': 'success'})
            self.payment.status = 'settled'
        else:
            self.payment.status = 'failed'
        self.payment.update_response = data
        self.payment.save()

        if self.payment.status == 'failed':
            raise PaymentException('Error processing payment')
