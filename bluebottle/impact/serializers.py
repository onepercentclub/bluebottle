from rest_framework import serializers
from rest_framework_json_api.serializers import ModelSerializer

from rest_framework_json_api.relations import PolymorphicResourceRelatedField

from bluebottle.impact.models import ImpactType, ImpactGoal
from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivitySerializer


class ImpactTypeSerializer(ModelSerializer):
    slug = serializers.SlugField(allow_null=True, required=False)
    name = serializers.CharField(required=True)
    unit = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = ImpactType
        fields = (
            'id', 'slug', 'name', 'unit',
        )

    class JSONAPIMeta:
        resource_name = 'activities/impact-types'


class ImpactGoalSerializer(ModelSerializer):
    target = serializers.FloatField()
    realized = serializers.FloatField(allow_null=True, required=False)

    activity = PolymorphicResourceRelatedField(ActivitySerializer, queryset=Activity.objects.all())

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
