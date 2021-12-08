from builtins import object
from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import SorlImageField
from bluebottle.activities.models import Activity
from bluebottle.initiatives.models import Initiative
from bluebottle.segments.models import Segment, SegmentType
from bluebottle.utils.fields import SafeField


class SegmentTypeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)

    included_serializers = {
        'segments': 'bluebottle.segments.serializers.SegmentSerializer',
    }

    class Meta(object):
        model = SegmentType
        fields = (
            'id', 'name', 'slug', 'enable_search', 'user_editable', 'segments'
        )

    class JSONAPIMeta(object):
        included_resources = ['segments', ]
        resource_name = 'segment-types'


class SegmentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    logo = SorlImageField('82x82', crop='center')
    cover_image = SorlImageField('384x288', crop='center')

    story = SafeField(required=False, allow_blank=True, allow_null=True)

    initiatives_count = serializers.SerializerMethodField()
    activities_count = serializers.SerializerMethodField()

    included_serializers = {
        'type': 'bluebottle.segments.serializers.SegmentTypeSerializer',
    }

    def get_initiatives_count(self, obj):
        return len(Initiative.objects.filter(status='approved', activities__segments=obj))

    def get_activities_count(self, obj):
        return len(Activity.objects.filter(segments=obj))

    class Meta(object):
        model = Segment
        fields = (
            'id', 'name', 'type', 'slug', 'tag_line', 'background_color',
            'text_color', 'logo', 'cover_image', 'story',
            'initiatives_count', 'activities_count',
        )
        meta_fields = ['initiatives_count', 'activities_count']

    class JSONAPIMeta(object):
        included_resources = ['type', ]
        resource_name = 'segments'
