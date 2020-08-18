from rest_framework_json_api.serializers import ModelSerializer

from rest_framework_json_api.relations import PolymorphicResourceRelatedField

from bluebottle.impact.models import ImpactType, ImpactGoal
from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivitySerializer


class ImpactTypeSerializer(ModelSerializer):
    class Meta:
        model = ImpactType
        fields = (
            'id', 'slug', 'unit',
            'text', 'text_with_target',
            'text_passed',
            'icon',
        )

    class JSONAPIMeta:
        resource_name = 'activities/impact-types'


class ImpactGoalSerializer(ModelSerializer):
    activity = PolymorphicResourceRelatedField(
        ActivitySerializer, queryset=Activity.objects.all())

    included_serializers = {
        'type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
    }

    class Meta:
        model = ImpactGoal
        fields = (
            'id', 'target', 'realized', 'activity', 'type',
        )

    class JSONAPIMeta:
        resource_name = 'activities/impact-goals'
        included_resources = ['type', 'activity']
