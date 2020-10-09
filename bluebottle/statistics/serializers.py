from builtins import str
from builtins import object
from rest_framework import serializers
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.statistics.models import (
    BaseStatistic, DatabaseStatistic, ManualStatistic, ImpactStatistic
)


class BaseStatisticSerializer(ModelSerializer):
    value = serializers.SerializerMethodField()

    def get_value(self, obj):
        value = obj.get_value()

        try:
            return {
                'amount': value.amount,
                'currency': str(value.currency)
            }
        except AttributeError:
            return value

        return value


class ManualStatisticSerializer(BaseStatisticSerializer):
    class Meta(object):
        model = ManualStatistic
        fields = ('id', 'value', 'name', 'icon')

    class JSONAPIMeta(object):
        resource_name = 'statistics/manual-statistics'
        fields = ('id', 'value', 'name', 'icon', )


class DatabaseStatisticSerializer(BaseStatisticSerializer):
    class Meta(object):
        model = DatabaseStatistic
        fields = ('id', 'value', 'name', 'query', 'icon', )

    class JSONAPIMeta(object):
        resource_name = 'statistics/database-statistics'


class ImpactStatisticSerializer(BaseStatisticSerializer):
    included_serializers = {
        'impact_type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
    }

    class Meta(object):
        model = ImpactStatistic
        fields = ('id', 'value', 'impact_type')

    class JSONAPIMeta(object):
        resource_name = 'statistics/impact-statistics'
        included_resources = ['impact_type']


class StatisticSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DatabaseStatisticSerializer,
        ManualStatisticSerializer,
        ImpactStatisticSerializer
    ]

    class Meta(object):
        model = BaseStatistic

    class JSONAPIMeta(object):
        included_resources = ['impact_type']
