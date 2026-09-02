from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.utils.utils import clean_html
from bluebottle.voting.models import Poll, PollOption


class PollOptionSerializer(ModelSerializer):
    title = serializers.CharField()
    description = serializers.SerializerMethodField()
    image = ImageSerializer(required=False, allow_null=True)
    video_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    sequence = serializers.IntegerField(read_only=True)

    class Meta:
        model = PollOption
        fields = (
            'id', 'title', 'description', 'image', 'video_url', 'sequence'
        )

    class JSONAPIMeta:
        resource_name = 'polls/options'

    def get_description(self, obj):
        value = obj.description
        if not value:
            return ''
        html = getattr(value, 'html', None)
        if not html:
            return ''
        return clean_html(html)


class PollSerializer(ModelSerializer):
    title = serializers.CharField()
    subtitle = serializers.CharField(required=False, allow_blank=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.CharField(read_only=True)
    options = ResourceRelatedField(many=True, read_only=True)

    class Meta:
        model = Poll
        fields = (
            'id', 'title', 'subtitle', 'end_date', 'status', 'options'
        )

    class JSONAPIMeta:
        resource_name = 'polls'
        included_resources = ['options']

    included_serializers = {
        'options': 'bluebottle.voting.serializers.PollOptionSerializer',
    }
