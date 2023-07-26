from builtins import object

from rest_framework import serializers
from rest_framework_json_api.relations import HyperlinkedRelatedField

from bluebottle.activities.models import Activity
from bluebottle.activities.utils import get_stats_for_activities
from bluebottle.bluebottle_drf2.serializers import SorlImageField
from bluebottle.initiatives.models import Initiative
from bluebottle.segments.models import Segment, SegmentType
from bluebottle.utils.fields import SafeField


class SegmentTypeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    segments = HyperlinkedRelatedField(
        many=True,
        read_only=True,
        related_link_view_name='related-segment-detail',
        related_link_url_kwarg='segment_type',
    )

    class Meta(object):
        model = SegmentType
        fields = (
            'id', 'name', 'slug', 'inherit', 'required',
            'enable_search', 'user_editable', 'segments'
        )

    class JSONAPIMeta(object):
        resource_name = 'segment-types'


class SegmentListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    logo = SorlImageField('180x180', crop='center')
    cover_image = SorlImageField('384x288', crop='center')

    story = SafeField(required=False, allow_blank=True, allow_null=True)

    included_serializers = {
        'segment_type': 'bluebottle.segments.serializers.SegmentTypeSerializer',
    }

    class Meta(object):
        model = Segment
        fields = (
            'id', 'name', 'segment_type', 'email_domains', 'slug', 'tag_line',
            'background_color', 'text_color',
            'button_color', 'button_text_color',
            'logo', 'cover_image', 'story', 'closed',
        )

    class JSONAPIMeta(object):
        included_resources = ['segment_type', ]
        resource_name = 'segments'


class SegmentDetailSerializer(SegmentListSerializer):
    initiatives_count = serializers.SerializerMethodField()
    activities_count = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    def get_initiatives_count(self, obj):
        return len(Initiative.objects.filter(status='approved', activities__segments=obj).distinct())

    def get_activities_count(self, obj):
        total = Activity.objects.filter(
            segments=obj,
            status__in=['open', 'full']
        ).count()
        return total

    def get_stats(self, obj):
        return get_stats_for_activities(obj.activities.all())

    class Meta(SegmentListSerializer.Meta):
        fields = SegmentListSerializer.Meta.fields + (
            'initiatives_count', 'activities_count', 'stats'
        )
        meta_fields = ['initiatives_count', 'activities_count', 'stats']


class SegmentPublicDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    logo = SorlImageField('180x180', crop='center')
    cover_image = SorlImageField('1280x720', crop='center')

    class Meta(object):
        model = Segment
        fields = (
            'id', 'name', 'logo', 'cover_image', 'email_domains', 'background_color', 'closed',
            'text_color'
        )

    class JSONAPIMeta(object):
        resource_name = 'segment-previews'
