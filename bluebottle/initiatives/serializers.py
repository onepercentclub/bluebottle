from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.bb_projects.models import ProjectTheme
from bluebottle.bluebottle_drf2.serializers import (
    OEmbedField, ImageSerializer as OldImageSerializer, SorlImageField
)
from bluebottle.categories.models import Category
from bluebottle.files.serializers import ImageField, ImageSerializer
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member
from bluebottle.utils.fields import SafeField, FSMField
from bluebottle.utils.serializers import (
    ResourcePermissionField
)


class ThemeSerializer(ModelSerializer):

    class Meta:
        model = ProjectTheme
        fields = ('id', 'slug', 'name', 'description')

    class JSONAPIMeta:
        resource_name = 'themes'


class CategorySerializer(ModelSerializer):
    image = OldImageSerializer(required=False)
    image_logo = OldImageSerializer(required=False)
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'title', 'slug', 'description', 'image', 'image_logo')

    class JSONAPIMeta:
        resource_name = 'categories'


class MemberSerializer(ModelSerializer):
    avatar = SorlImageField('133x133', source='picture', crop='center')
    full_name = serializers.ReadOnlyField(source='get_full_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    short_name = serializers.ReadOnlyField(source='get_short_name', read_only=True)

    class Meta:
        model = Member
        fields = ('id', 'first_name', 'last_name', 'initials', 'avatar', 'full_name', 'short_name', 'is_active')

    class JSONAPIMeta:
        resource_name = 'user-previews'


class InitiativeImageSerializer(ImageSerializer):
    sizes = {
        'preview': '200x300',
        'large': '400x500'
    }
    content_view_name = 'initiative-image'


class InitiativeSerializer(ModelSerializer):
    image = ImageField(required=False, allow_null=True)
    owner = ResourceRelatedField(read_only=True)
    permissions = ResourcePermissionField('initiative-detail', view_args=('pk',))
    review_status = FSMField(read_only=True)
    reviewer = ResourceRelatedField(read_only=True)
    slug = serializers.CharField(read_only=True)
    story = SafeField(required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(allow_blank=True, required=False)
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')

    included_serializers = {
        'categories': 'bluebottle.initiatives.serializers.CategorySerializer',
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'place': 'bluebottle.geo.serializers.InitiativePlaceSerializer',
        'reviewer': 'bluebottle.initiatives.serializers.MemberSerializer',
        'theme': 'bluebottle.initiatives.serializers.ThemeSerializer',
    }

    class Meta:
        model = Initiative
        fields = (
            'id', 'title', 'pitch', 'review_status', 'categories', 'owner', 'reviewer', 'slug',
            'story', 'video_html', 'image', 'theme', 'place', 'permissions',
        )

    class JSONAPIMeta:
        included_resources = ['owner', 'reviewer', 'categories', 'theme', 'place', 'image']
        resource_name = 'initiatives'
