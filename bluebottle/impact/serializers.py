from builtins import object
from rest_framework_json_api.serializers import ModelSerializer

from rest_framework_json_api.relations import PolymorphicResourceRelatedField

from bluebottle.impact.models import ImpactType, ImpactGoal
from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivitySerializer


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
        ActivitySerializer, queryset=Activity.objects.all())

    included_serializers = {
        'type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
    }

    class Meta(object):
        model = ImpactGoal
        fields = (
            'id', 'target', 'realized', 'activity', 'type',
        )

    class JSONAPIMeta(object):
        resource_name = 'activities/impact-goals'
        included_resources = ['type', 'activity']
