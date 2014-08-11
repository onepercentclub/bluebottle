from bluebottle.payments.serializers import BasePaymentMetaDataSerializer
from bluebottle.payments_mollie.models import MolliePayment
from rest_framework import serializers


class PaymentMethodSerializer(BasePaymentMetaDataSerializer):

    class Meta:
        model = MolliePayment
        fields = BasePaymentMetaDataSerializer.Meta.fields + ('issuer', 'redirect_url', 'method')