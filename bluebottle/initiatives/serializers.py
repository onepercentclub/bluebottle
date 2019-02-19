from rest_framework import serializers
from rest_framework_json_api.serializers import ModelSerializer
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.bluebottle_drf2.serializers import (
    OEmbedField
)
from bluebottle.files.serializers import FileField
from bluebottle.initiatives.models import Initiative, Theme
from bluebottle.categories.serializers import CategorySerializer
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.utils.fields import SafeField, FSMField
from bluebottle.utils.serializers import (
    ResourcePermissionField, FSMModelSerializer
)


class ThemeSerializer(ModelSerializer):
    class Meta:
        model = Theme
        fields = ('id', 'slug', 'name', 'description')


class InitiativeSerializer(FSMModelSerializer):
    review_status = FSMField(required=False)
    story = SafeField(required=False)
    slug = serializers.CharField(read_only=True)

    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')

    image = FileField(
        required=False,
        content_view_name='initiative-image',
        sizes=['200x300', '400x500']
    )

    owner = ResourceRelatedField(read_only=True)
    reviewer = ResourceRelatedField(read_only=True)
    permissions = ResourcePermissionField('initiative-detail', view_args=('pk',))

    included_serializers = {
        'owner': 'bluebottle.members.serializers.UserPreviewSerializer',
        'reviewer': 'bluebottle.members.serializers.UserPreviewSerializer',
        'categories': 'bluebottle.categories.serializers.CategorySerializer',
        'theme': 'bluebottle.initiatives.serializers.ThemeSerializer',
    }

    class Meta:
        model = Initiative
        fields = (
            'id', 'title', 'review_status', 'categories', 'owner', 'reviewer', 'slug',
            'story', 'video_html', 'image', 'theme', 'permissions',
        )

    class JSONAPIMeta:
        included_resources = ['owner']
