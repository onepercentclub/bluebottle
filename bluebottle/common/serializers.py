from bluebottle.common.models import CommonPlatformSettings

from rest_framework import serializers


class CommonPlatformSettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommonPlatformSettings
        fields = (
            'lockdown',
        )
