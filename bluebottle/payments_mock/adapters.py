# coding=utf-8
import re
from bluebottle.payments.exception import PaymentException
from django.core.urlresolvers import reverse
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.utils.utils import StatusDefinition
from bluebottle.payments.models import OrderPayment
from .models import MockPayment


class MockPaymentAdapter(BasePaymentAdapter):
    MODEL_CLASSES = [MockPayment]

    def create_payment(self):
        """
        Have some basic criteria that might fail so we can check our error parsing.
        """
        if self.order_payment.amount < 10:
            raise PaymentException("Amount for Mock payments should be greater then 10")

        user_data = self.get_user_data()
        pattern = re.compile(r'\W')
        if pattern.findall(user_data['first_name']):
            raise PaymentException("First name '{0}' has got illegal characters.".format(user_data['first_name']))

        if len(user_data['last_name']) > 30:
            raise PaymentException("Last name too long: '{0}'".format(user_data["last_name"]))

        # Now just create the payment.
        payment = self.MODEL_CLASSES[0](order_payment=self.order_payment)
        payment.save()
        return payment

    def get_authorization_action(self):
        """
        This is the PSP url where Ember redirects the user to.
        """
        return {'type': 'redirect',
                'method':'get',
                'url': reverse('payment-service-provider', kwargs={'order_payment_id': self.order_payment.id})}

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
        pass
