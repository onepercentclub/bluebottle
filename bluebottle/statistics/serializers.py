from rest_framework import serializers

from bluebottle.statistics.models import Statistic


class StatisticSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='calculated_value')

    class Meta:
        model = Statistic
        fields = ('id', 'title', 'type', 'value', 'language')
