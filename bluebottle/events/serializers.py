from bluebottle.activities.serializers import BaseActivitySerializer, ContributionSerializer
from bluebottle.events.models import Event, Participant


class EventSerializer(BaseActivitySerializer):
    class Meta:
        model = Event
        fields = BaseActivitySerializer.Meta.fields + (
            'start', 'end', 'registration_deadline', 'capacity',
            'address'
        )


class ParticipantSerializer(ContributionSerializer):
    class Meta:
        model = Participant
        fields = ContributionSerializer.Meta.fields + ('time_spent', )
