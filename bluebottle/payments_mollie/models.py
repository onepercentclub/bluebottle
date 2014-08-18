from bluebottle.payments.models import Transaction, Payment, PaymentMetaDataType, PaymentMetaDataMethod
from django.db import models
import Mollie


class MolliePayment(Payment):
    description = models.CharField(max_length=200, default='')
    method = models.CharField(max_length=200, default=Mollie.API.Object.Method.IDEAL)
    issuer = models.CharField(max_length=200, default='')
    redirect_url = models.CharField(max_length=200, default='')
    payment_url = models.CharField(max_length=200, default='')
    status = models.CharField(max_length=200, default='')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    meta_data = models.CharField(max_length=2000, default='')

    class Meta:
        serializer = 'bluebottle.payments_mollie.serializers.MolliePaymentSerializer'


class MollieTransaction(Transaction):
    pass
