from rest_framework import serializers

from bluebottle.segments.models import Segment, SegmentType


class SegmentTypeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)

    included_serializers = {
        'segments': 'bluebottle.segments.serializers.SegmentSerializer',
    }

    class Meta:
        model = SegmentType
        fields = ('id', 'name', 'slug', 'enable_search', 'segments')

    class JSONAPIMeta:
        included_resources = ['segments', ]
        resource_name = 'segment-types'


class SegmentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)

    included_serializers = {
        'type': 'bluebottle.segments.serializers.SegmentTypeSerializer',
    }

    class Meta:
        model = Segment
        fields = ('id', 'name', 'type')

    class JSONAPIMeta:
        included_resources = ['type', ]
        resource_name = 'segments'
