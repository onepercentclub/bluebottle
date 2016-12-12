from rest_framework import serializers

from bluebottle.statistics.models import Statistic


class StatisticSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    def get_value(self, obj):
        value = obj.calculated_value
        try:
            return u"{0}".format(int(round(value.amount, 0)))
        except AttributeError:
            return u"{0}".format(value)

    class Meta:
        model = Statistic
        fields = ('id', 'title', 'type', 'value', 'language')
