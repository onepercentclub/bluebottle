from rest_framework import serializers

from bluebottle.events.models import Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'created', 'updated')
