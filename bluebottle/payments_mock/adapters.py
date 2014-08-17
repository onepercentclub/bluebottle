# coding=utf-8
import time
import unicodedata
from bluebottle.payments.adapters import AbstractPaymentAdapter
from bluebottle.payments.models import PaymentStatuses, PaymentLogLevels
from django.conf import settings
from django.utils.http import urlencode
from .models import MolliePayment, MollieTransaction
import Mollie


class MolliePaymentAdapter(AbstractPaymentAdapter):

    status_mapping = {
        'NEW': PaymentStatuses.new,
        'STARTED': PaymentStatuses.in_progress,
        'REDIRECTED_FOR_AUTHENTICATION': PaymentStatuses.in_progress,
        'AUTHORIZED': PaymentStatuses.pending,
        'AUTHORIZATION_REQUESTED': PaymentStatuses.pending,
        'PAID': PaymentStatuses.pending,
        'CANCELED': PaymentStatuses.cancelled,
        'CHARGED-BACK': PaymentStatuses.chargedback,
        'CONFIRMED_PAID': PaymentStatuses.paid,
        'CONFIRMED_CHARGEDBACK': PaymentStatuses.chargedback,
        'CLOSED_SUCCESS': PaymentStatuses.paid,
        'CLOSED_CANCELED': PaymentStatuses.cancelled,
    }

    def get_return_url(self, payment):
        return 'http://localhost:8000/#!/orders/1/success'

    def create_payment(self, order_payment, meta_data=None, **kwargs):
        payment = MolliePayment(**meta_data)
        payment.payment_order = order_payment
        payment.save()
        return payment

    def get_authorization_action(self, order_payment):
        if order_payment.paymen_method == 'mockIdeal':
            payment = MockIdealPayment()

        mollie = Mollie.API.Client()
        mollie.setApiKey(settings.MOLLIE_API_KEY)

        # Generate Mollie Payment
        mollie_payment = mollie.payments.create({
            'amount': payment.amount,
            'description': payment.description,
            'redirectUrl': self.get_return_url(payment)
        })
        payment.payment_url = mollie_payment.paymentUrl
        payment.status = mollie_payment.status

        return mollie_payment.paymentUrl


