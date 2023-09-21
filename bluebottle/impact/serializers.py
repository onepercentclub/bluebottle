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
    }

    class Meta(object):
        model = ImpactGoal
        fields = (
            'id', 'target', 'realized', 'realized_from_contributions', 'activity', 'type',
            'required', 'errors', 'participant_impact', 'impact_realized'
        )
        meta_fields = ['errors', 'required']

    class JSONAPIMeta(object):
        resource_name = 'activities/impact-goals'
        included_resources = ['type']
