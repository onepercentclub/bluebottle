from builtins import object
from rest_framework import serializers

from bluebottle.notifications.models import NotificationPlatformSettings


class NotificationPlatformSettingsSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = NotificationPlatformSettings

        fields = (
            'share_options',
            'facebook_at_work_url',
            'default_yammer_group_id',
        )
