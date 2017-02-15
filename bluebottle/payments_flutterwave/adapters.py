# coding=utf-8
import json

from bluebottle.payments.exception import PaymentException
from django.db import connection

from flutterwave import Flutterwave

from bluebottle.payments.adapters import BasePaymentAdapter
from .models import FlutterwavePayment
from bluebottle.utils.utils import get_current_host


class FlutterwavePaymentAdapter(BasePaymentAdapter):
    MODEL_CLASSES = [FlutterwavePayment]

    card_data = {}
    live = False

    def create_payment(self):
        """
        Create a new payment
        """
        self.card_data = self.order_payment.card_data
        payment = self.MODEL_CLASSES[0](order_payment=self.order_payment,
                                        card_number="**** **** **** " + self.card_data['card_number'][-4:]
                                        )
        if 'pin' in self.card_data:
            payment.auth_model = 'PIN'
        else:
            payment.auth_model = 'VBVSECURECODE'
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
                          {'debug': self.debug})

        card_data = self.card_data
        pin = ''
        cvv = ''
        if 'pin' in card_data:
            pin = card_data['pin']
        if 'cvv' in card_data:
            cvv = card_data['cvv']
        data = {
            "amount": self.payment.amount,
            "currency": self.payment.currency,
            "authModel": self.payment.auth_model,
            "cardNumber": card_data['card_number'],
            "cvv": cvv,
            "expiryMonth": card_data['expiry_month'],
            "expiryYear": card_data['expiry_year'],
            "pin": pin,
            "customerID": self.payment.customer_id,
            "narration": self.payment.narration,
            "responseUrl": self.payment.response_url,
            "country": self.payment.country
        }

        print json.dumps(data)

        r = flw.card.charge(data)
        response = json.loads(r.text)
        self.payment.response = "{}".format(r.text)
        self.payment.save()
        if response['status'] == u'error':
            raise PaymentException('Flutterwave error: {0}'.format(response['data']))
        if response['data']['responsecode'] == u'00':
            self.payment.status = 'authorized'
            self.payment.save()
            return {'type': 'success'}
        if response['data']['responsecode'] in [u'7', u'RR']:
            self.payment.status = 'failed'
            self.payment.save()
            raise PaymentException('Error starting payment: {0}'.format(response['data']['responsemessage']))
        if 'authurl' in response['data'] and response['data']['authurl']:
            return {
                'method': 'get',
                'url': response['data']['authurl'],
                'type': 'redirect',
                'payload': {
                    'method': 'flutterwave-otp',
                    'text': response['data']['responsemessage'],

                }
            }

        return {
            'type': 'step2',
            'payload': {
                'method': 'flutterwave-otp',
                'text': response['data']['responsemessage']
            }
        }

    def check_payment_status(self):
        flw = Flutterwave(self.credentials['api_key'],
                          self.credentials['merchant_key'],
                          {'debug': self.debug})

        transaction_reference = self.payment.transaction_reference
        card_data = self.order_payment.card_data
        if 'otp' in card_data:
            otp = card_data['otp']
            data = {
                "otp": otp,
                "otpTransactionIdentifier": self.payment.transaction_reference,
                "country": "NG"
            }
            r = flw.card.validate(data)
            response = json.loads(r.text)
            if response['data']['responsecode'] == u'00':
                self.order_payment.set_authorization_action({'type': 'success'})
                self.payment.status = 'settled'
        else:
            r = flw.card.verifyCharge(transactionRef=transaction_reference, country='NG')
            response = json.loads(r.text)
            if response['data']['responsecode'] == u'00':
                self.payment.status = 'settled'
            if response['data']['responsecode'] == u'7':
                self.payment.status = 'failed'
            if response['data']['responsemessage'] == u'Declined':
                self.payment.status = 'failed'
        self.payment.update_response = response
        self.payment.save()
