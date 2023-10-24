from builtins import object

from rest_framework_json_api.relations import PolymorphicResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivitySerializer
from bluebottle.impact.models import ImpactType, ImpactGoal
from bluebottle.utils.fields import ValidationErrorsField, RequiredErrorsField


class ImpactTypeSerializer(ModelSerializer):
    class Meta(object):
        model = ImpactType
        fields = (
            'id', 'slug', 'name', 'unit',
            'text', 'text_with_target',
            'text_passed',
            'icon',
        )

    class JSONAPIMeta(object):
        resource_name = 'activities/impact-types'


class ImpactGoalSerializer(ModelSerializer):
    activity = PolymorphicResourceRelatedField(
        ActivitySerializer, queryset=Activity.objects.all()
    )

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
        'activity': 'bluebottle.activities.serializers.ActivitySerializer',
    }

    def to_internal_value(self, data):
        # Change '' to None
        data['target'] = data.get('target', None) or None
        data['participant_target'] = data.get('participant_target', None) or None
        return super().to_internal_value(data)

    class Meta(object):
        model = ImpactGoal
        fields = (
            'id',
            'target',
            'participant_target',
            'impact_realized',
            'realized',
            'realized_from_contributions',
            'activity',
            'type',
            'required',
            'errors',
            'participant_impact',
        )
        meta_fields = ['errors', 'required']

    class JSONAPIMeta(object):
        resource_name = 'activities/impact-goals'
        included_resources = ['type', 'activity']
