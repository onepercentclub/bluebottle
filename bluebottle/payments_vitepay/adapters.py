# coding=utf-8
import hashlib
import json
import requests

from bluebottle.payments.exception import PaymentException
from moneyed import XOF

from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments_vitepay.models import VitepayPayment
from bluebottle.utils.utils import get_current_host, StatusDefinition


class VitepayPaymentAdapter(BasePaymentAdapter):

    MODEL_CLASSES = [VitepayPayment]

    fields = ['language_code',
              'currency_code',
              'country_code',
              'order_id',
              'description',
              'amount_100',
              'buyer_ip_adress',
              'return_url',
              'decline_url',
              'cancel_url',
              'callback_url',
              'email',
              'p_type']

    def _get_return_host(self):
        host = get_current_host()
        if '8000' in host:
            host.replace('8000', '4200')
        return host

    def _get_callback_host(self):
        host = get_current_host()
        if '8000' in host:
            host = 'https://nexteconomy.com'
        return host

    def create_payment(self):
        """
        Create a new payment
        """

        if self.order_payment.amount.currency != XOF:
            raise PaymentException("Can only do Vitepay payments in XOF, Communauté Financière Africaine (BCEAO).")

        if self.merchant != 'vitepay':
            raise PaymentException("Not a VitePay order-payment. Merchant is {0}".format(self.merchant))

        payment = self.MODEL_CLASSES[0].objects.create(order_payment=self.order_payment)
        # Amount on the payment should be in CFA * 100
        payment.amount_100 = int(self.order_payment.amount.amount * 100)
        payment.description = "Thanks for your donation!"
        payment.callback_url = '{0}/payments_vitepay/payment_response/{1}'.format(
            self._get_callback_host(),
            self.order_payment.id)

        payment.return_url = '{0}/orders/{1}/success'.format(
            self._get_return_host(),
            self.order_payment.order.id)

        payment.decline_url = '{0}/orders/{1}/failed'.format(
            self._get_return_host(),
            self.order_payment.order.id)

        payment.cancel_url = '{0}/orders/{1}/failed'.format(
            self._get_return_host(),
            self.order_payment.order.id)

        payment.order_id = 'opc-{0}'.format(self.order_payment.id)
        payment.save()
        return payment

    def _create_payment_hash(self):
        """
        Le hash est une valeur calculée avec la formule suivante :
        SHA1(UPPERCASE("order_id;amount_100;currency_code;callback_url;api_secret"))
        Concaténez les différentes valeurs order_id, amount_100, currency_code,
        callback_url et api-secret en utilisant ; (point-virgule)comme séparateur
        Faites passer toute la chaîne en majuscules
        Appliquer la fonction SHA1(SHA1)

        api_secret : Cette information vous est transmise par VitePay
        lors de l'enregistrement de votre site marchand. Contactez l'adminsitrateur
        du site pour lequel vous souhaitez faire l'intégration pour récupérer cette information.
        """
        api_secret = self.credentials['api_secret']
        message = "{p.order_id};{p.amount_100};{p.currency_code};" \
                  "{p.callback_url};{api_secret}".format(p=self.payment, api_secret=api_secret)
        return hashlib.sha1(message.upper()).hexdigest()

    def _get_payment_url(self):
        data = {
            "language_code": "en",
            "currency_code": "XOF",
            "country_code": "ML",
            "order_id": self.payment.order_id,
            "description": self.payment.description,
            "amount_100": self.payment.amount,
            "return_url": self.payment.return_url,
            "decline_url": self.payment.decline_url,
            "cancel_url": self.payment.cancel_url,
            "callback_url": self.payment.callback_url,
            "p_type": "orange_money",
            "redirect": "0",
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

    def _get_mapped_status(self, status):
        """
        Helper to map the status of a PSP specific status (Mock PSP) to our own status pipeline for an OrderPayment.
        The status of a MockPayment maps 1-1 to OrderStatus so we can return the status
        """
        return status

    def _create_update_hash(self):
        """
        Cette information permet de sécuriser la communication serveur-à-serveur.
        En effet, vous devez recalculer cette chaîne au niveau de votre intégration et
        la comparer à celle que nous vous transmettons. Ne modifier votre panier que
        s'il y a une correspondance parfaite.

        Littéralement, authenticity est la valeur SHA1 de la concaténation du numéro
        de comande, montant de de la transaction (x100), devise et signature du site marchand.
        authenticity = SHA1("order_id;amount_100;currency_code;api_secret")
        """
        api_secret = self.credentials['api_secret']
        message = "{p.order_id};{p.amount_100};{p.currency_code};" \
                  "{api_secret}".format(p=self.payment, api_secret=api_secret)
        return hashlib.sha1(message.upper()).hexdigest()

    def status_update(self, authenticity, success, failure):
        if authenticity != self._create_update_hash():
            raise PaymentException('Authenticity incorrect.')
        elif success and failure:
            raise PaymentException('Both failure and succes are set. Not sure what to do.')
        elif not success and  not failure:
            raise PaymentException('Both failure and succes are unset. Not sure what to do.')
        elif failure:
            self.payment.status = StatusDefinition.FAILED
        else:
            self.payment.status = StatusDefinition.SETTLED
        self.payment.save()
        return True
