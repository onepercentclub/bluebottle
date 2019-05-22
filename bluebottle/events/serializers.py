from bluebottle.activities.utils import BaseActivitySerializer, BaseContributionSerializer
from bluebottle.events.models import Event, Participant
from bluebottle.utils.serializers import ResourcePermissionField


class EventSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('event-detail', view_args=('pk',))

    class Meta:
        model = Event
        fields = BaseActivitySerializer.Meta.fields + (
            'permissions',
            'location',
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


class ParticipantSerializer(BaseContributionSerializer):
    class Meta:
        model = Participant
        fields = BaseContributionSerializer.Meta.fields + ('time_spent', )
