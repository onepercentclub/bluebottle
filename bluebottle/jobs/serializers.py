from bluebottle.activities.utils import BaseContributionSerializer, BaseActivitySerializer
from bluebottle.events.models import Event, Participant


class JobSerializer(BaseActivitySerializer):
    class Meta:
        model = Event
        fields = BaseActivitySerializer.Meta.fields + (
            'start', 'end', 'registration_deadline', 'capacity',
            'address'
        )


class JobParticipantSerializer(BaseContributionSerializer):
    class Meta:
        model = Participant
        fields = BaseContributionSerializer.Meta.fields + ('time_spent', )
