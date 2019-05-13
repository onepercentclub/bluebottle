from bluebottle.activities.serializers import BaseActivitySerializer, ContributionSerializer
from bluebottle.events.models import Event, Participant
from bluebottle.utils.serializers import ResourcePermissionField


class EventSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('event-detail', view_args=('pk',))

    class Meta:
        model = Event
        fields = BaseActivitySerializer.Meta.fields + (
            'permissions',
            'address',
            'capacity',
            'end',
            'registration_deadline',
            'start',
        )

    class JSONAPIMeta:
        included_resources = [
            'owner',
            'initiative'
        ]
        resource_name = 'events'


class ParticipantSerializer(ContributionSerializer):
    class Meta:
        model = Participant
        fields = ContributionSerializer.Meta.fields + ('time_spent', )
