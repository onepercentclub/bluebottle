from bluebottle.payments.models import Payment, PaymentMetaData
from rest_framework import serializers


class PaymentMethodSerializer(serializers.Serializer):

    class Meta:
        fields = ('name', 'profile', )


class BasePaymentMetaDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentMetaData
        fields = ('payment', 'created', 'updated', 'type', 'method')


class PolymorphicPaymentMetaDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentMetaData

    def to_native(self, obj):
        """
        Because PaymentMetaData is Polymorphic
        """
        if obj:
            return obj.__class__._meta.serializer
        return None


class ManagePaymentSerializer(serializers.ModelSerializer):

    status = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(read_only=True)
    integration_data = serializers.SerializerMethodField('get_data_serializer')

    def get_data_serializer(self, obj):
        meta_data = obj.meta_data
        serializer_context = {'request': self.context.get('request'),
                              'payment_id': obj.id}
        serializer = PolymorphicPaymentMetaDataSerializer(meta_data, context=serializer_context)
        return serializer.data

    class Meta:
        model = Payment
        fields = ('amount', 'order', 'payment_method', 'integration_data')

