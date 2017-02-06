# coding=utf-8
import json
from django.db import connection

from flutterwave import Flutterwave

from bluebottle.payments.adapters import BasePaymentAdapter
from .models import FlutterwavePayment
from bluebottle.utils.utils import get_current_host


class FlutterwavePaymentAdapter(BasePaymentAdapter):

    MODEL_CLASSES = [FlutterwavePayment]

    def create_payment(self):
        """
        Create a new payment
        """
        payment = self.MODEL_CLASSES[0](order_payment=self.order_payment,
                                        **self.order_payment.integration_data)
        if getattr(self.order_payment.integration_data, 'pin', None):
            payment.auth_model = 'PIN'
        elif getattr(self.order_payment.integration_data, 'bvn', None):
            payment.auth_model = 'BVN'
        elif getattr(self.order_payment.integration_data, 'bvn', None):
            payment.auth_model = 'NOAUTH'
        else:
            payment.auth_model = 'RANDOM_DEBIT'
        payment.amount = str(self.order_payment.amount.amount)
        payment.currency = str(self.order_payment.amount.currency)
        payment.customer_id = str(self.order_payment.user or 1)
        payment.narration = "Donation {0}".format(self.order_payment.id)
        payment.response_url = '{0}/payments_flutterwave/payment_response/{1}'.format(
            get_current_host(),
            self.order_payment.id)
        tenant = connection.tenant
        payment.site_name = str(tenant.domain_url)
        try:
            payment.cust_id = self.order_payment.user.id
            payment.cust_name = str(self.order_payment.user.full_name)
        except AttributeError:
            # Anonymous order
            pass
        payment.txn_ref = '{0}-{1}'.format(tenant.name, self.order_payment.id)
        payment.save()
        return payment

    def get_authorization_action(self):
        """
        Handle payment
        """

        flw = Flutterwave(self.credentials['api_key'],
                          self.credentials['merchant_key'],
                          {"debug": True})

        data = {
            "amount": self.payment.amount,
            "currency": self.payment.currency,
            "authModel": self.payment.auth_model,
            "cardNumber": self.payment.card_number,
            "cvv": self.payment.cvv,
            "expiryMonth": self.payment.expiry_month,
            "expiryYear": self.payment.expiry_year,
            "bvn": self.payment.bvn or '',
            "pin": self.payment.pin or '',
            "customerID": self.payment.customer_id,
            "narration": self.payment.narration,
            "responseUrl": self.payment.response_url,
            "country": self.payment.country
        }

        r = flw.card.charge(data)
        response = json.loads(r.text)
        self.payment.response = "{}".format(r.text)
        self.payment.save()
        if response['data']['responsecode'] == u'00':
            self.payment.status = 'authorized'
            self.payment.save()
            return {'type': 'success'}

        return {
            'type': 'step2',
            'payload': {
                'text': response['data']['responsemessage']
            }
        }

    def check_payment_status(self):
        flw = Flutterwave(self.credentials['api_key'],
                          self.credentials['merchant_key'],
                          {"debug": True})

        transactionRef = self.payment.transaction_reference
        r = flw.card.verifyCharge(transactionRef=transactionRef, country='NG')
        response = json.loads(r.text)
        if response['data']['responsecode'] == u'00':
            self.payment.status = 'settled'
        self.payment.update_response = response
        self.payment.save()
