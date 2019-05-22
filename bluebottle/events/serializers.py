from bluebottle.activities.utils import BaseActivitySerializer, BaseContributionSerializer
from bluebottle.events.models import Event, Participant
from bluebottle.utils.serializers import ResourcePermissionField


class EventSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('event-detail', view_args=('pk',))

    class Meta:
        model = Event
        fields = BaseActivitySerializer.Meta.fields + (
            'permissions',
            'capacity',
            'end',
            'location',
            'registration_deadline',
            'start',
        )

    class JSONAPIMeta:
        included_resources = [
            'owner',
            'initiative',
            'location'
        ]
        resource_name = 'events'

    included_serializers = {
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'location': 'bluebottle.geo.serializers.ActivityPlaceSerializer',
    }


class ParticipantSerializer(BaseContributionSerializer):
    class Meta:
        model = Participant
        fields = BaseContributionSerializer.Meta.fields + ('time_spent', )
