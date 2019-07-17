from bluebottle.funding.serializers import PaymentSerializer
from bluebottle.funding_lipisha.models import LipishaPayment
from bluebottle.funding_lipisha.utils import initiate_push_payment


class LipishaPaymentSerializer(PaymentSerializer):

    class Meta(PaymentSerializer.Meta):
        model = LipishaPayment
        fields = PaymentSerializer.Meta.fields + ('mobile_number', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/lipisha-payments'

    def create(self, validated_data):
        payment = super(LipishaPaymentSerializer, self).create(validated_data)
        payment = initiate_push_payment(payment)
        return payment
