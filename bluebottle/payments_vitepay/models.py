# -*- coding: utf-8 -*-
from decimal import Decimal

from django.db import models

from bluebottle.payments.models import Payment


class VitepayPayment(Payment):

    # en, fr default is fr
    language_code = models.CharField(max_length=10, default='en')

    # Currency code (ISO-4217), default is XOF, Communauté Financière Africaine (BCEAO)
    currency_code = models.CharField(max_length=10, default='XOF')

    # Country code, default is ML (Mali)
    country_code = models.CharField(max_length=10, default='ML')

    # Unique payment id. Trying to create a new payment with an id
    # already used results in an error.
    order_id = models.CharField(max_length=10, null=True)

    # Description (max 160 chars). Required for VitePay payment.
    description = models.CharField(max_length=500, null=True)

    # Amount of the payment in CFA * 100.
    amount_100 = models.IntegerField(null=True)

    # Customer IP (not required)
    buyer_ip_adress = models.CharField(max_length=200, null=True)

    # Return url for success
    return_url = models.CharField(max_length=500, null=True)

    # Return url for declined payments
    decline_url = models.CharField(max_length=500, null=True)

    # Return url for canceled payments
    cancel_url = models.CharField(max_length=500, null=True)

    # Callback url where VitePay sends the payment status update
    callback_url = models.CharField(max_length=500, null=True)

    # Email of customer (not required)
    email = models.CharField(max_length=500, null=True)

    # Payment type, default (and only option) is 'orange_money'.
    p_type = models.CharField(max_length=500, default='orange_money')

    payment_url = models.CharField(max_length=500, null=True)

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = "Vitepay Payment"
        verbose_name_plural = "Vitepay Payments"

    @property
    def transaction_reference(self):
        return self.order_id

    def get_method_name(self):
        """ Return the payment method name."""
        return 'vitepay'

    def get_fee(self):
        """
        Currently the fee is 2%.
        """
        fee = round(self.order_payment.amount * Decimal(0.02), 2)
        return fee
