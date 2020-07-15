from rest_framework import serializers
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.statistics.models import (
    BaseStatistic, DatabaseStatistic, ManualStatistic, ImpactStatistic
)


class BaseStatisticSerializer(ModelSerializer):
    value = serializers.SerializerMethodField()

    def get_value(self, obj):
        return obj.get_value()


class ManualStatisticSerializer(BaseStatisticSerializer):
    class Meta:
        model = ManualStatistic
        fields = ('id', 'value', 'name', )

    class JSONAPIMeta:
        resource_name = 'statistics/manual-statistics'
        fields = ('id', 'value', 'name', )


class DatabaseStatisticSerializer(BaseStatisticSerializer):
    class Meta:
        model = DatabaseStatistic
        fields = ('id', 'value', 'name', 'query',)

    class JSONAPIMeta:
        resource_name = 'statistics/database-statistics'


class ImpactStatisticSerializer(BaseStatisticSerializer):
    included_serializers = {
        'impact_type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
    }

    class Meta:
        model = ImpactStatistic
        fields = ('id', 'value', 'impact_type')

    class JSONAPIMeta:
        resource_name = 'statistics/impact-statistics'
        included_resources = ['impact_type']


class StatisticSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DatabaseStatisticSerializer,
        ManualStatisticSerializer,
        ImpactStatisticSerializer
    ]

    class Meta:
        model = BaseStatistic

    class JSONAPIMeta:
        included_resources = ['impact_type']
