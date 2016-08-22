# coding=utf-8
import hashlib

import urllib2
import simplejson
from bluebottle.payments.exception import PaymentException
from moneyed import NGN

from bluebottle.clients import properties
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments_interswitch.models import InterswitchPayment
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
        payment.product_id = properties.INTERSWITCH_PRODUCT_ID
        payment.pay_item_id = properties.INTERSWITCH_ITEM_ID
        # Amount on the payment should be in kobo/cents
        payment.amount = int(self.order_payment.amount.amount * 100)
        if self.order_payment.amount.currency != NGN:
            raise PaymentException("Can only do Interswitch payments in Nigerian Naira (NGN).")

        payment.site_redirect_url = '{0}/payments_interswitch/payment_response/{1}'.format(
                get_current_host(),
                self.order_payment.id)

        payment.txn_ref = 'opc-{0}'.format(self.order_payment.id)


        payment.save()
        return payment

    def _get_create_hash(self):
        """
        SHA512 of combined data:
        txn_ref
        product_id
        pay_item_id
        amount
        site_redirect_url
        hashkey
        """
        hashkey = properties.INTERSWITCH_HASHKEY
        message = "{p.txn_ref}{p.product_id}{p.pay_item_id}" \
                  "{p.amount}{p.site_redirect_url}{hashkey}".format(
                p=self.payment, hashkey=hashkey)
        return hashlib.sha512(message).hexdigest()

    def _get_status_hash(self):
        """
        SHA512 of combined data:
        txn_ref
        product_id
        hashkey
        """
        hashkey = properties.INTERSWITCH_HASHKEY
        message = "{p.product_id}{p.txn_ref}{hashkey}".format(
                p=self.payment, hashkey=hashkey)
        return hashlib.sha512(message).hexdigest()

    def _get_payload(self):
        payload = {}
        for field in self.fields:
            payload[field] = getattr(self.payment, field)
        payload['hash'] = self._get_create_hash()
        return payload

    def get_authorization_action(self):
        """
        This is the PSP url where Ember redirects the user to.
        """
        payload = self._get_payload()

        return {'type': 'redirect',
                'method': 'post',
                'payload': payload,
                'url': properties.INTERSWITCH_PAYMENT_URL}

    def _get_mapped_status(self, status):
        """
        Helper to map the status of a PSP specific status (Mock PSP) to our own status pipeline for an OrderPayment.
        The status of a MockPayment maps 1-1 to OrderStatus so we can return the status
        """
        return status

    def set_order_payment_new_status(self, status):
        self.order_payment.transition_to(self._get_mapped_status(status))
        return self.order_payment

    def check_payment_status(self):
        status_url = properties.INTERSWITCH_STATUS_URL
        url = "{0}?productid={1}&transactionreference={2}&amount={3}".format(
            status_url, self.payment.product_id, self.payment.txn_ref, self.payment.amount
        )
        print url
        print hash
        req = urllib2.Request(url, headers={"Hash" : self._get_status_hash()})
        opener = urllib2.build_opener()
        f = opener.open(req)
        result = simplejson.load(f)

        self.payment.result = f
        self.payment.save()

        if 'ResponseDescription' in result and result['ResponseDescription'] == 'Approved Successful':
            self.payment.status = StatusDefinition.SETTLED
            self.payment.save()

