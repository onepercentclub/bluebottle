from rest_framework import serializers

from bluebottle.impact.models import ImpactType, ImpactGoal
from rest_framework_json_api.serializers import ModelSerializer


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
        resource_name = 'impact-types'


class ImpactGoalSerializer(ModelSerializer):
    target = serializers.FloatField()
    realized = serializers.FloatFieldField(allow_null=True, required=False)

    included_serializers = {
        'type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
    }

    class Meta:
        model = ImpactGoal
        fields = (
            'id', 'target', 'realized',
        )

    class JSONAPIMeta:
        resource_name = 'impact-goal'
        included_resources = ['type', ]
