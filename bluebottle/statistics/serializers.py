from rest_framework import serializers


class StatisticSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='id')
    donated = serializers.DecimalField(source='donated')
    projects_online = serializers.IntegerField(source='projects_online')
    projects_realized = serializers.IntegerField(source='projects_realized')
    tasks_realized = serializers.IntegerField(source='tasks_realized')
    people_involved = serializers.IntegerField(source='people_involved')

    class Meta:
        fields = ('id', 'donated', 'projects_online', 'projects_realized',
                  'tasks_realized', 'people_involved')
