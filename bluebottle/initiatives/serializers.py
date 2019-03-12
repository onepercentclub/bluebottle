from rest_framework import serializers
from rest_framework_json_api.serializers import ModelSerializer
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.bluebottle_drf2.serializers import (
    OEmbedField, ImageSerializer, SorlImageField
)
from bluebottle.initiatives.models import Initiative, Theme
from bluebottle.categories.serializers import CategorySerializer
from bluebottle.categories.models import Category
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.members.models import Member
from bluebottle.utils.fields import SafeField, FSMField
from bluebottle.utils.serializers import (
    ResourcePermissionField, FSMModelSerializer
)


class ThemeSerializer(ModelSerializer):
    class Meta:
        model = Theme
        fields = ('id', 'slug', 'name', 'description')

    class JSONAPIMeta:
        resource_name = 'themes'


class CategorySerializer(ModelSerializer):
    slug = serializers.CharField(read_only=True)
    image = ImageSerializer(required=False)
    image_logo = ImageSerializer(required=False)

    class Meta:
        model = Category
        fields = ('id', 'title', 'slug', 'description', 'image', 'image_logo')

    class JSONAPIMeta:
        resource_name = 'categories'


class MemberSerializer(ModelSerializer):
    avatar = SorlImageField('133x133', source='picture', crop='center')
    full_name = serializers.ReadOnlyField(source='get_full_name', read_only=True)
    short_name = serializers.ReadOnlyField(source='get_short_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Member
        fields = ('id', 'first_name', 'last_name', 'initials', 'avatar', 'full_name', 'short_name', 'is_active')

    class JSONAPIMeta:
        resource_name = 'user-previews'


class InitiativeSerializer(ModelSerializer):
    review_status = FSMField(read_only=True)
    story = SafeField(required=False)
    title = serializers.CharField(allow_blank=True, required=False)
    slug = serializers.CharField(read_only=True)

    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    image = ImageSerializer(required=False)
    owner = ResourceRelatedField(read_only=True)
    reviewer = ResourceRelatedField(read_only=True)
    permissions = ResourcePermissionField('initiative-detail', view_args=('pk',))

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'reviewer': 'bluebottle.initiatives.serializers.MemberSerializer',
        'categories': 'bluebottle.initiatives.serializers.CategorySerializer',
        'theme': 'bluebottle.initiatives.serializers.ThemeSerializer',
    }

    class Meta:
        model = Initiative
        fields = (
            'id', 'title', 'review_status', 'categories', 'owner', 'reviewer', 'slug',
            'story', 'video_html', 'image', 'theme', 'permissions',
        )

    class JSONAPIMeta:
        included_resources = ['owner', 'reviewer', 'categories', 'theme',]
        resource_name = 'initiatives'
