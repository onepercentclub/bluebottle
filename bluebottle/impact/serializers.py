from builtins import object

from rest_framework_json_api.relations import PolymorphicResourceRelatedField, ResourceRelatedField
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
    impact_type = ResourceRelatedField(source='type', queryset=ImpactType.objects.all())

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'impact_type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
        'activity': 'bluebottle.activities.serializers.ActivitySerializer',
    }

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
            'impact_type',
            'required',
            'errors',
            'participant_impact',
        )
        meta_fields = ['errors', 'required']

    class JSONAPIMeta(object):
        resource_name = 'activities/impact-goals'
        included_resources = ['impact_type', 'activity']
