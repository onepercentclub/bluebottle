# coding=utf-8
import hashlib
import requests

import simplejson
from django.db import connection

from bluebottle.payments.exception import PaymentException
from moneyed import NGN

from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments_interswitch.models import InterswitchPayment, InterswitchPaymentStatusUpdate
from bluebottle.utils.utils import get_current_host, StatusDefinition


class InterswitchPaymentAdapter(BasePaymentAdapter):

    MODEL_CLASSES = [InterswitchPayment]

    fields = ['product_id',
              'amount',
              'currency',
              'site_redirect_url',
              'txn_ref',
              'hash',
              'pay_item_id',
              'site_name',
              'cust_id',
              'cust_id_desc',
              'cust_name',
              'cust_name_desc',
              'pay_item_name',
              'local_date_time']

    def create_payment(self):
        """
        Create a new payment
        """
        payment = self.MODEL_CLASSES[0](order_payment=self.order_payment)
        payment.product_id = self.credentials['product_id']
        payment.pay_item_id = self.credentials['item_id']
        # Amount on the payment should be in kobo/cents
        payment.amount = int(self.order_payment.amount.amount * 100)
        if self.order_payment.amount.currency != NGN:
            raise PaymentException("Can only do Interswitch payments in Nigerian Naira (NGN).")
        payment.site_redirect_url = '{0}/payments_interswitch/payment_response/{1}'.format(
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
        return payment

    def _create_hash(self):
        """
        SHA512 of combined data:
        txn_ref
        product_id
        pay_item_id
        amount
        site_redirect_url
        hashkey
        """
        hashkey = self.credentials['hashkey']
        message = "{p.txn_ref}{p.product_id}{p.pay_item_id}" \
                  "{p.amount}{p.site_redirect_url}{hashkey}".format(p=self.payment, hashkey=hashkey)
        return hashlib.sha512(message).hexdigest()

    def _get_status_hash(self):
        """
        SHA512 of combined data:
        txn_ref
        product_id
        hashkey
        """
        hashkey = self.credentials['hashkey']
        message = "{p.product_id}{p.txn_ref}{hashkey}".format(p=self.payment, hashkey=hashkey)
        return hashlib.sha512(message).hexdigest()

    def _get_payload(self):
        payload = {}
        for field in self.fields:
            payload[field] = getattr(self.payment, field)
        payload['hash'] = self._create_hash()
        return payload

    def get_authorization_action(self):
        """
        This is the PSP url where Ember redirects the user to.
        """
        payload = self._get_payload()

        return {'type': 'redirect',
                'method': 'post',
                'payload': payload,
                'url': self.credentials['payment_url']}

    def check_payment_status(self):
        status_url = self.credentials['status_url']
        url = "{0}?productid={1}&transactionreference={2}&amount={3}".format(
            status_url, self.payment.product_id, self.payment.txn_ref, self.payment.amount
        )
        response = requests.get(url, headers={"Hash": self._get_status_hash()}).content
        self.payment.response = response

        InterswitchPaymentStatusUpdate.objects.create(payment=self.payment, result=response)

        result = simplejson.loads(response)
        if 'ResponseCode' in result and result['ResponseCode'] == '00':
            self.payment.status = StatusDefinition.SETTLED
        else:
            self.payment.status = StatusDefinition.FAILED

        self.payment.save()
