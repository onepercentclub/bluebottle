from builtins import object
from bluebottle.analytics.models import AnalyticsPlatformSettings, AnalyticsAdapter

from rest_framework import serializers


class AnalyticsAdapterSerializer(serializers.ModelSerializer):

    class Meta(object):
        fields = (
            'code',
            'type'
        )
        model = AnalyticsAdapter


class AnalyticsPlatformSettingsSerializer(serializers.ModelSerializer):

    adapters = AnalyticsAdapterSerializer(many=True)

    class Meta(object):
        model = AnalyticsPlatformSettings
        fields = (
            'adapters',
        )
