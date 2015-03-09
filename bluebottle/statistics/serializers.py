from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from rest_framework import serializers
from bluebottle.bluebottle_drf2.serializers import EuroField
from .models import Statistic


class StatisticSerializer(serializers.ModelSerializer):
    donated = serializers.DecimalField(source='donated')
    projects_online = serializers.DecimalField(source='projects_online')
    projects_realized = serializers.DecimalField(source='projects_realized')
    tasks_realized = serializers.DecimalField(source='tasks_realized')
    people_involved = serializers.DecimalField(source='people_involved')

    class Meta:
        model = Statistic
        fields = ('donated', 'projects_online', 'projects_realized', 'tasks_realized', 'people_involved')
