import datetime
from builtins import object
from builtins import str

from dateutil.relativedelta import relativedelta
from django.utils.timezone import get_current_timezone
from django_tools.middlewares.ThreadLocal import get_current_user
from rest_framework import serializers
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.statistics.models import (
    BaseStatistic, DatabaseStatistic, ManualStatistic, ImpactStatistic
)

tz = get_current_timezone()


class BaseStatisticSerializer(ModelSerializer):
    value = serializers.SerializerMethodField()

    def get_user(self):
        return None

    def get_value(self, obj):
        params = self.context['request'].query_params
        start = None
        end = None
        subregion = None
        user = self.get_user()

        if 'filter[year]' in params:
            year = int(params['filter[year]'])
            settings = MemberPlatformSettings.load()
            start = datetime.datetime(year, 1, 1, tzinfo=tz) + relativedelta(months=settings.fiscal_month_offset)
            end = datetime.datetime(year, 12, 31, tzinfo=tz) + relativedelta(months=settings.fiscal_month_offset)

        current_user = get_current_user()

        if 'filter[type]' in params and current_user:
            if (
                params['filter[type]'] == 'office_region' and 
                current_user.location and 
                current_user.location.subregion and
                current_user.location.subregion.region
            ):
                region = current_user.location.subregion.region
                value = obj.get_value(start, end, region=region)
            elif (
                params['filter[type]'] == 'office_subregion'
                current_user.location and 
                current_user.location.subregion and
            ):
                subregion = current_user.location.subregion
                value = obj.get_value(start, end, subregion=subregion)
            else:
                value = obj.get_value(start, end)
        else:
            if user:
                value = obj.get_live_value(start, end, user=user)
            else:
                value = obj.get_value(start, end)

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


class UserStatisticSerializer(StatisticSerializer):

    def get_user(self):
        return get_current_user()
