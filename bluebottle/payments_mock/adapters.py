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
            MockPayment.STATUS_CHOICES.StatusDefinition.CREATED: OrderPayment.STATUS_CHOICES.StatusDefinition.CREATED,
            MockPayment.STATUS_CHOICES.StatusDefinition.STARTED: OrderPayment.STATUS_CHOICES.StatusDefinition.STARTED,
            MockPayment.STATUS_CHOICES.StatusDefinition.AUTHORIZED: OrderPayment.STATUS_CHOICES.StatusDefinition.AUTHORIZED,
            MockPayment.STATUS_CHOICES.StatusDefinition.SETTLED: OrderPayment.STATUS_CHOICES.StatusDefinition.SETTLED,
            MockPayment.STATUS_CHOICES.StatusDefinition.FAILED: OrderPayment.STATUS_CHOICES.StatusDefinition.FAILED,
            MockPayment.STATUS_CHOICES.StatusDefinition.CANCELLED: OrderPayment.STATUS_CHOICES.StatusDefinition.CANCELLED,
            MockPayment.STATUS_CHOICES.StatusDefinition.CHARGED_BACK: OrderPayment.STATUS_CHOICES.StatusDefinition.CHARGED_BACK,
            MockPayment.STATUS_CHOICES.StatusDefinition.REFUNDED: OrderPayment.STATUS_CHOICES.StatusDefinition.REFUNDED,
            MockPayment.STATUS_CHOICES.StatusDefinition.UNKNOWN: OrderPayment.STATUS_CHOICES.StatusDefinition.UNKNOWN,
        }
        return status_mapping.get(status, OrderPayment.STATUS_CHOICES.StatusDefinition.UNKNOWN)

    def set_order_payment_new_status(self, status):
        self.order_payment.status = self._get_mapped_status(status)
        self.order_payment.save()
        return self.order_payment

    def check_payment_status(self):
        pass
