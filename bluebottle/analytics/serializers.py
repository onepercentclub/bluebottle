from bluebottle.analytics.models import AnalyticsPlatformSettings, AnalyticsAdapter

from rest_framework import serializers


class AnalyticsAdapterSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'code',
            'type'
        )
        model = AnalyticsAdapter


class AnalyticsPlatformSettingsSerializer(serializers.ModelSerializer):

    adapters = AnalyticsAdapterSerializer(many=True)

    class Meta:
        model = AnalyticsPlatformSettings
        fields = (
            'adapters',
        )
