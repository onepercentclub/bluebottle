# coding=utf-8
from django.core.urlresolvers import reverse
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments.models import OrderPaymentStatuses
from .models import MockPayment, MockPaymentStatuses

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
        Helper to map the status of a PSP specific status to our own status pipeline
        """
        status_mapping = {
            MockPaymentStatuses.created: OrderPaymentStatuses.created,
            MockPaymentStatuses.started: OrderPaymentStatuses.started,
            MockPaymentStatuses.authorized: OrderPaymentStatuses.authorized,
            MockPaymentStatuses.settled: OrderPaymentStatuses.settled,
            MockPaymentStatuses.failed: OrderPaymentStatuses.failed,
            MockPaymentStatuses.cancelled: OrderPaymentStatuses.cancelled,
            MockPaymentStatuses.chargedback: OrderPaymentStatuses.chargedback,
            MockPaymentStatuses.refunded: OrderPaymentStatuses.refunded,
            MockPaymentStatuses.unknown: OrderPaymentStatuses.unknown,
        }
        return status_mapping.get(status, OrderPaymentStatuses.unknown)

    def set_order_payment_new_status(self, order_payment, status):
        order_payment.status = self._get_mapped_status(status)
        order_payment.save()
        return order_payment


