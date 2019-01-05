from rest_framework import serializers

from bluebottle.kyc.models import AccountVerification


class VerificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccountVerification
        fields = (
            'user',
            'organization',
        )
