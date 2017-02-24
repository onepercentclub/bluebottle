# coding=utf-8
import json
import logging

from django.db import connection
from flutterwave import Flutterwave

from bluebottle.clients import properties
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments.exception import PaymentException
from bluebottle.utils.utils import get_current_host
from .models import FlutterwavePayment

logger = logging.getLogger(__name__)


SUCCESS_RESPONSECODES = ['0', '00']


class FlutterwavePaymentAdapter(BasePaymentAdapter):
    MODEL_CLASSES = [FlutterwavePayment]

    card_data = {}

    def create_payment(self):
        """
        Create a new payment
        """
        self.card_data = self.order_payment.card_data
        if not {'card_number', 'expiry_month', 'expiry_year', 'cvv'}.issubset(self.card_data):
            logger.warn('payment_tracer: {}, '
                        'event: payment.flutterwave.invalid_credentials,'
                        'card_number: {}, '
                        'expiry_month: {}, '
                        'expiry_year: {}, '
                        'cvv: {}'.format(self.payment_tracer,
                                         getattr(self.card_data, 'card_number', None),
                                         getattr(self.card_data, 'expiry_month', None),
                                         getattr(self.card_data, 'expiry_year', None),
                                         getattr(self.card_data, 'cvv', None)
                                         ))
            raise PaymentException('Card number, expiry month/year and cvv is required')

        payment = self.MODEL_CLASSES[0](order_payment=self.order_payment,
                                        card_number="**** **** **** " + self.card_data['card_number'][-4:]
                                        )
        if 'pin' in self.card_data and self.card_data['pin']:
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
            payment.cust_name = unicode(self.order_payment.user.full_name)
        except AttributeError:
            # Anonymous order
            pass
        payment.txn_ref = '{0}-{1}'.format(tenant.name, self.order_payment.id)
        payment.save()
        self.payment_logger.log(payment,
                                'info',
                                'payment_tracer: {}, '
                                'event: payment.flutterwave.create_payment.success'.format(self.payment_tracer))
        return payment

    def get_authorization_action(self):
        """
        Handle payment
        """
        options = {'debug': True}

        if properties.LIVE_PAYMENTS_ENABLED:
            options = {
                'debug': False,
                'env': 'production'
            }

        flw = Flutterwave(self.credentials['api_key'],
                          self.credentials['merchant_key'],
                          options)

        card_data = self.card_data
        pin = ''
        cvv = ''
        if 'pin' in card_data:
            pin = card_data['pin']
        if 'cvv' in card_data:
            cvv = card_data['cvv']

        if not {'card_number', 'expiry_month', 'expiry_year', 'cvv'}.issubset(self.card_data):
            logger.warn('payment_tracer: {}, '
                        'event: payment.flutterwave.invalid_credentials,'
                        'card_number: {}, '
                        'expiry_month: {}, '
                        'expiry_year: {}, '
                        'cvv: {}'.format(self.payment_tracer,
                                         getattr(self.card_data, 'card_number', None),
                                         getattr(self.card_data, 'expiry_month', None),
                                         getattr(self.card_data, 'expiry_year', None),
                                         getattr(self.card_data, 'cvv', None)
                                         ))
            raise PaymentException('Card number, expiry month/year and cvv is required')

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

        logger.info('payment_tracer: {}, '
                    'event: payment.flutterwave.get_authorization_action.request'
                    'amount: {}, '
                    'currency: {}, '
                    'authModel: {}, '
                    'cardNumber: {}, '
                    'cvv: {}, '
                    'expiryMonth: {}, '
                    'expiryYear: {}, '
                    'pin: {}, '
                    'customerId: {}, '
                    'narration: {}, '
                    'responseUrl: {}, '
                    'country: {}'.format(self.payment_tracer,
                                         self.payment.amount,
                                         self.payment.currency,
                                         self.payment.auth_model,
                                         card_data['card_number'][-4:],
                                         cvv,
                                         card_data['expiry_month'],
                                         card_data['expiry_year'],
                                         pin,
                                         self.payment.customer_id,
                                         self.payment.narration,
                                         self.payment.response_url,
                                         self.payment.country)
                    )
        r = flw.card.charge(data)
        if r.status_code == 500:
            logger.warn('payment_tracer: {}, '
                        'event: payment.flutterwave.error.500, '
                        'flutterwave_response: {}'.format(self.payment_tracer,
                                                          r.text)
                        )
            raise PaymentException('Flutterwave could not confirm your card details, please try again.')
        response = json.loads(r.text)

        self.payment.response = "{}".format(r.text)
        self.payment.save()

        logger.info('payment_tracer: {}, '
                    'event: payment.flutterwave.get_authorization_action.response, '
                    'flutterwave_response: {}'.format(self.payment_tracer,
                                                      r.text
                                                      ))

        if response['status'] == u'error':
            logger.warn('payment_tracer: {}, '
                        'event: payment.flutterwave.get_authorization_action.error, '
                        'flutterwave_response: {}'.format(self.payment_tracer,
                                                          response['data']
                                                          ))
            raise PaymentException('Flutterwave error: {0}'.format(response['data']))

        if response['data']['responsecode'] in SUCCESS_RESPONSECODES:
            self.payment.status = 'authorized'
            self.payment.save()
            logger.info('payment_tracer: {}, '
                        'event: payment.flutterwave.get_authorization_action.authorized, '
                        'response: {}'.format(self.payment_tracer,
                                              response['data']
                                              ))
            return {'type': 'success'}

        if response['data']['responsecode'] == '02':
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
            else:
                return {
                    'type': 'step2',
                    'payload': {
                        'method': 'flutterwave-otp',
                        'text': response['data']['responsemessage']
                    }
                }

        logger.warn('payment_tracer: {}, '
                    'event: payment.flutterwave.get_authorization_action.error.start_payment '
                    'flutterwave_response: {}'.format(self.payment_tracer,
                                                      response['data']
                                                      ))
        raise PaymentException('Error starting payment: {0}'.format(response['data']['responsemessage']))

    def check_payment_status(self):

        options = {'debug': True}

        if properties.LIVE_PAYMENTS_ENABLED:
            options = {
                'debug': False,
                'env': 'production'
            }

        flw = Flutterwave(self.credentials['api_key'],
                          self.credentials['merchant_key'],
                          options)

        transaction_reference = self.payment.transaction_reference
        card_data = self.order_payment.card_data or {}
        if 'otp' in card_data:
            otp = card_data['otp']
            data = {
                "otp": otp,
                "otpTransactionIdentifier": self.payment.transaction_reference,
                "country": "NG"
            }
            logger.info('payment_tracer: {}, '
                        'event: payment.flutterwave.payment_status.otp_validate.request, '
                        'flutterwave_request: {}'.format(self.payment_tracer,
                                                         data
                                                         ))
            r = flw.card.validate(data)
            response = json.loads(r.text)
            if response['data']['responsecode'] in SUCCESS_RESPONSECODES:
                self.order_payment.set_authorization_action({'type': 'success'})
                self.payment.status = 'settled'
            else:
                self.payment.status = 'failed'
        else:
            r = flw.card.verifyCharge(transactionRef=transaction_reference, country='NG')
            response = json.loads(r.text)
            if response['data']['responsecode'] in SUCCESS_RESPONSECODES:
                self.payment.status = 'settled'
            if response['data']['responsecode'] == u'7':
                self.payment.status = 'failed'
            if response['data']['responsemessage'] == u'Declined':
                self.payment.status = 'failed'

        logger.info('payment_tracer: {}, '
                    'transaction_reference: {}, '
                    'event: payment.flutterwave.payment_status, '
                    'flutterwave_response: {}'.format(self.payment_tracer,
                                                      transaction_reference,
                                                      response['data']
                                                      ))
        self.payment.update_response = response
        self.payment.save()

        if self.payment.status == 'failed':
            raise PaymentException(response['data']['responsemessage'])
