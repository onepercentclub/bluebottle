from django.contrib.contenttypes.models import ContentType


from rest_framework import serializers


from bluebottle.accounts.serializers import UserPreviewSerializer
from bluebottle.bluebottle_drf2.serializers import (SorlImageField, SlugGenericRelatedField, PolymorphicSerializer, EuroField,
                                              TagSerializer, ImageSerializer, TaggableSerializerMixin, OEmbedField)
from bluebottle.geo.models import Country
from bluebottle.utils.serializers import MetaField

from django.conf import settings

#from apps.fund.models import Donation
from .models import Project, ProjectTheme
#from apps.wallposts.models import TextWallPost, MediaWallPost
#from apps.wallposts.serializers import TextWallPostSerializer, MediaWallPostSerializer

from .models import Project


class ProjectCountrySerializer(serializers.ModelSerializer):

    subregion = serializers.CharField(source='subregion.name')

    class Meta:
        model = Country
        fields = ('id', 'name', 'subregion')


class ProjectSerializer(serializers.ModelSerializer):

    id = serializers.CharField(source='slug', read_only=True)
    owner = UserPreviewSerializer()
    image = ImageSerializer(required=False)

    meta_data = MetaField(
            title = 'get_meta_title',
            fb_title = 'get_fb_title',
            description = 'pitch',
            keywords = 'tags',
            image_source = 'image',
            tweet = 'get_tweet',
            )

    def __init__(self, *args, **kwargs):
        super(ProjectSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Project
        fields = ('id', 'created', 'title', 'pitch', 'description', 'owner', 'phase', 'meta_data', 'image')


class ProjectPreviewSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    image = SorlImageField('image', '400x300', crop='center')
    country = ProjectCountrySerializer(source='country')
    pitch = serializers.CharField(source='pitch')

    class Meta:
        model = Project
        fields = ('id', 'title', 'image', 'phase', 'country')


class ProjectEditableField(serializers.BooleanField):

    pass


class ManageProjectSerializer(TaggableSerializerMixin, serializers.ModelSerializer):

    id = serializers.CharField(source='slug', read_only=True)

    url = serializers.HyperlinkedIdentityField(view_name='project-manage-detail')
    phase = serializers.CharField(read_only=True)
    editable = ProjectEditableField(read_only=True, source=phase)
    tags = TagSerializer()
    organization = serializers.PrimaryKeyRelatedField(source="organization", required=False)
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    editable = serializers.BooleanField(read_only=True)

    image = ImageSerializer(required=False)

    class Meta:
        model = Project
        fields = ('id', 'created', 'title', 'url', 'phase', 'image', 'pitch', 'tags', 'description',
                  'country', 'latitude', 'longitude', 'reach', 'organization',
                  'image', 'video_html', 'video_url', 'money_needed', 'editable')


class ProjectThemeSerializer(serializers.ModelSerializer):
    title = serializers.Field(source='name')

    class Meta:
        model = ProjectTheme
        fields = ('id', 'title')
