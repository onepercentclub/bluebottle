# coding=utf-8
from django.core.urlresolvers import reverse
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.utils.utils import StatusDefinition
from bluebottle.payments.models import OrderPayment
from .models import MockPayment


class MockPaymentAdapter(BasePaymentAdapter):
    MODEL_CLASS = MockPayment

    def create_payment(self):
        payment = self.MODEL_CLASS(order_payment=self.order_payment)
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
        Helper to map the status of a PSP specific status (Mock PSP) to our own status pipeline for an OrderPayment
        """
        status_mapping = {
            dict(MockPayment.STATUS_CHOICES).get(StatusDefinition.CREATED): dict(OrderPayment.STATUS_CHOICES).get(StatusDefinition.CREATED),
            dict(MockPayment.STATUS_CHOICES).get(StatusDefinition.STARTED): dict(OrderPayment.STATUS_CHOICES).get(StatusDefinition.STARTED),
            dict(MockPayment.STATUS_CHOICES).get(StatusDefinition.AUTHORIZED): dict(OrderPayment.STATUS_CHOICES).get(StatusDefinition.AUTHORIZED),
            dict(MockPayment.STATUS_CHOICES).get(StatusDefinition.SETTLED): dict(OrderPayment.STATUS_CHOICES).get(StatusDefinition.SETTLED),
            dict(MockPayment.STATUS_CHOICES).get(StatusDefinition.FAILED): dict(OrderPayment.STATUS_CHOICES).get(StatusDefinition.FAILED),
            dict(MockPayment.STATUS_CHOICES).get(StatusDefinition.CANCELLED): dict(OrderPayment.STATUS_CHOICES).get(StatusDefinition.CANCELLED),
            dict(MockPayment.STATUS_CHOICES).get(StatusDefinition.CHARGED_BACK): dict(OrderPayment.STATUS_CHOICES).get(StatusDefinition.CHARGED_BACK),
            dict(MockPayment.STATUS_CHOICES).get(StatusDefinition.REFUNDED): dict(OrderPayment.STATUS_CHOICES).get(StatusDefinition.REFUNDED),
            dict(MockPayment.STATUS_CHOICES).get(StatusDefinition.UNKNOWN) : dict(OrderPayment.STATUS_CHOICES).get(StatusDefinition.UNKNOWN),
        }
        return status_mapping.get(status, dict(OrderPayment.STATUS_CHOICES).get(StatusDefinition.UNKNOWN))

    def set_order_payment_new_status(self, status):
        self.order_payment.status = self._get_mapped_status(status)
        self.order_payment.save()
        return self.order_payment

    def check_payment_status(self):
        pass
