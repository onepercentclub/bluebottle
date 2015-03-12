from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from bluebottle.bluebottle_drf2.serializers import EuroField
from rest_framework import serializers

from .models import Statistic


class StatisticSerializer(serializers.ModelSerializer):
    donated = serializers.DecimalField(source='donated')
    projects_online = serializers.IntegerField(source='projects_online')
    projects_realized = serializers.IntegerField(source='projects_realized')
    tasks_realized = serializers.IntegerField(source='tasks_realized')
    people_involved = serializers.IntegerField(source='people_involved')

    class Meta:
        model = Statistic
        fields = ('donated', 'projects_online', 'projects_realized', 'tasks_realized', 'people_involved')
