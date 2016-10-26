# coding=utf-8
import hashlib
import json
import requests
from urlparse import urljoin

from django.core.urlresolvers import reverse
from moneyed import XOF

from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments.exception import PaymentException
from bluebottle.payments_vitepay.models import VitepayPayment
from bluebottle.utils.utils import get_current_host, StatusDefinition


class VitepayPaymentAdapter(BasePaymentAdapter):

    MODEL_CLASSES = [VitepayPayment]

    def _get_callback_url(self):
        host = get_current_host()
        if 'localhost' in host:
            # Use a mocked url that will always return the expected result
            return 'http://www.mocky.io/v2/5810a2873a0000a1056097c7'

        return urljoin(host, reverse('vitepay-status-update'))

    def create_payment(self):
        """
        Create a new payment
        """

        if self.order_payment.amount.currency != XOF:
            raise PaymentException("Can only do Vitepay payments in XOF, Communauté Financière Africaine (BCEAO).")

        if self.merchant != 'vitepay':
            raise PaymentException("Not a VitePay order-payment. Merchant is {0}".format(self.merchant))

        payment = self.MODEL_CLASSES[0](order_payment=self.order_payment)
        # Amount on the payment should be in CFA * 100
        payment.amount_100 = int(self.order_payment.amount.amount * 100)
        payment.description = "Thanks for your donation!"
        payment.callback_url = self._get_callback_url()
        payment.return_url = '{0}/orders/{1}/success'.format(
            get_current_host(),
            self.order_payment.order.id)

        payment.decline_url = '{0}/orders/{1}/failed'.format(
            get_current_host(),
            self.order_payment.order.id)

        payment.cancel_url = '{0}/orders/{1}/failed'.format(
            get_current_host(),
            self.order_payment.order.id)

        payment.order_id = 'opc-{0}'.format(self.order_payment.id)
        payment.save()
        return payment

    def _create_payment_hash(self):
        """
        Calculate hash value for payment creation.

        hash = SHA1("order_id;amount_100;currency_code;callback_url;api_secret")
        """
        api_secret = self.credentials['api_secret']
        message = "{p.order_id};{p.amount_100};{p.currency_code};" \
                  "{p.callback_url};{api_secret}".format(p=self.payment, api_secret=api_secret)
        return hashlib.sha1(message.upper()).hexdigest()

    def _get_payment_url(self):
        """
        Get payment url from VitePay to redirect the user to.
        """
        data = {
            "payment": {
                "language_code": "fr",
                "currency_code": "XOF",
                "country_code": "ML",
                "order_id": self.payment.order_id,
                "description": self.payment.description,
                "amount_100": self.payment.amount_100,
                "return_url": self.payment.return_url,
                "decline_url": self.payment.decline_url,
                "cancel_url": self.payment.cancel_url,
                "callback_url": self.payment.callback_url,
                "p_type": "orange_money",
            },
            "redirect": 0,
            "api_key": self.credentials['api_key'],
            "hash": self._create_payment_hash()
        }
        url = self.credentials['api_url']
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            self.payment.payment_url = response.content
        else:
            raise PaymentException('Error creating payment: {0}'.format(response.content))
        self.payment.status = StatusDefinition.STARTED
        self.payment.save()
        return response.content

    def get_authorization_action(self):
        """
        This is the PSP url where Ember redirects the user to.
        """
        return {'type': 'redirect',
                'method': 'get',
                'url': self._get_payment_url()}

    def _create_update_hash(self):
        """
        Create hash value to compare with the received 'authenticity' value.

        authenticity = SHA1("order_id;amount_100;currency_code;api_secret")
        """
        api_secret = self.credentials['api_secret']
        message = '{order_id};{amount};{currency};{api_secret}'.format(
            order_id=self.payment.order_id.upper(),
            amount=self.payment.amount_100,
            currency=self.payment.currency_code,
            api_secret=api_secret
        )

        return hashlib.sha1(message).hexdigest().upper()

    def check_payment_status(self):
        pass

    def status_update(self, authenticity, success, failure):
        """
        Check the received status update and update payment status accordingly.
        Note: We can't check status from our site. We have to rely on VitePay sending
        us an update.
        """
        if authenticity != self._create_update_hash():
            raise PaymentException('Authenticity incorrect.')
        elif success and failure:
            raise PaymentException('Both failure and succes are set. Not sure what to do.')
        elif not success and not failure:
            raise PaymentException('Both failure and succes are unset. Not sure what to do.')
        elif failure:
            self.payment.status = StatusDefinition.FAILED
        else:
            self.payment.status = StatusDefinition.SETTLED
        self.payment.save()
        return True
