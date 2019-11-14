from rest_framework import serializers

from bluebottle.notifications.models import NotificationPlatformSettings


class NotificationPlatformSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPlatformSettings

        fields = (
            'share_options',
            'facebook_at_work_url',
            'match_options'
        )
