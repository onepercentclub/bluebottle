from rest_framework import serializers


class PaymentMethodSerializer(serializers.Serializer):

    class Meta:
        fields = ('name', 'profile', )

