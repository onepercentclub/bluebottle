import datetime
from builtins import object
from builtins import str

from dateutil.relativedelta import relativedelta
from django.utils.timezone import get_current_timezone
from rest_framework import serializers
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.statistics.models import (
    BaseStatistic, DatabaseStatistic, ManualStatistic, ImpactStatistic
)

tz = get_current_timezone()


class BaseStatisticSerializer(ModelSerializer):
    value = serializers.SerializerMethodField()

    def get_value(self, obj):
        params = self.context['request'].query_params
        if 'year' in params:
            year = int(params['year'])
            settings = MemberPlatformSettings.load()
            start = datetime.datetime(year, 1, 1, tzinfo=tz) + relativedelta(months=settings.fiscal_month_offset)
            end = datetime.datetime(year, 12, 31, tzinfo=tz) + relativedelta(months=settings.fiscal_month_offset)
            value = obj.get_value(start, end)
        else:
            value = obj.get_value()

        try:
            return {
                'amount': value.amount,
                'currency': str(value.currency)
            }
        except AttributeError:
            return value


class ManualStatisticSerializer(BaseStatisticSerializer):
    class Meta(object):
        model = ManualStatistic
        fields = ('value', 'name', 'icon', 'sequence')

    class JSONAPIMeta(object):
        resource_name = 'statistics/manual-statistics'


class DatabaseStatisticSerializer(BaseStatisticSerializer):
    class Meta(object):
        model = DatabaseStatistic
        fields = ('value', 'name', 'query', 'icon', 'sequence')

    class JSONAPIMeta(object):
        resource_name = 'statistics/database-statistics'


class ImpactStatisticSerializer(BaseStatisticSerializer):
    included_serializers = {
        'impact_type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
    }

    class Meta(object):
        model = ImpactStatistic
        fields = ('value', 'impact_type', 'sequence')

    class JSONAPIMeta(object):
        resource_name = 'statistics/impact-statistics'
        included_resources = ['impact_type']


class OldStatisticSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DatabaseStatisticSerializer,
        ManualStatisticSerializer,
        ImpactStatisticSerializer
    ]

    class Meta(object):
        model = BaseStatistic

    class JSONAPIMeta(object):
        included_resources = ['impact_type']


class StatisticSerializer(BaseStatisticSerializer):
    class Meta(object):
        model = ManualStatistic
        fields = ('value', 'name', 'icon', 'sequence', 'unit')

    class JSONAPIMeta(object):
        resource_name = 'statistics'
