# coding=utf-8
from django.db import connection

from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.utils.utils import get_current_host

from .models import TelesomPayment


class TelesomPaymentAdapter(BasePaymentAdapter):
    MODEL_CLASSES = [TelesomPayment]

    card_data = {}

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
        return {'type': 'success'}

    def check_payment_status(self):
        pass
