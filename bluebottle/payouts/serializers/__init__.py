from rest_framework import serializers

from bluebottle.payouts.models import PayoutAccount
from bluebottle.payouts.models.plain import PlainPayoutAccount
from bluebottle.payouts.models.stripe import StripePayoutAccount
from bluebottle.payouts.serializers.plain import PlainPayoutAccountSerializer
from bluebottle.payouts.serializers.stripe import StripePayoutAccountSerializer
from bluebottle.utils.serializers import MoneySerializer
from ..models import ProjectPayout


from rest_polymorphic.serializers import PolymorphicSerializer


class BasePayoutAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = PayoutAccount
        fields = ('id', 'created')


class PayoutAccountSerializer(PolymorphicSerializer):

    resource_type_field_name = 'type'

    def to_resource_type(self, model_or_instance):
        return model_or_instance.type

    model_serializer_mapping = {
        PayoutAccount: BasePayoutAccountSerializer,
        StripePayoutAccount: StripePayoutAccountSerializer,
        PlainPayoutAccount: PlainPayoutAccountSerializer
    }

    def update(self, instance, validated_data):
        pass


class PayoutMethodSerializer(serializers.Serializer):

    class Meta:
        fields = (
            'type',
            'countries',
            'data'
        )


# Legacy serializer

class PayoutSerializer(serializers.ModelSerializer):

    amount = MoneySerializer(source='amount_payable')

    class Meta:
        model = ProjectPayout
        fields = ('id', 'amount', 'project',
                  'receiver_account_number',
                  'receiver_account_iban',
                  'receiver_account_details',
                  'receiver_account_name',
                  'receiver_account_city',
                  'receiver_account_country'
                  )
