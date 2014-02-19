from rest_framework import serializers
from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from bluebottle.bluebottle_drf2.serializers import (
    SorlImageField, TagSerializer, ImageSerializer, TaggableSerializerMixin,
    OEmbedField)
from bluebottle.geo.models import Country

from bluebottle.bb_projects import get_project_model
from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase
from bluebottle.utils.serializers import MetaField
from bluebottle.geo.serializers import CountrySerializer


PROJECT_MODEL = get_project_model()


class ProjectPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase


class ProjectCountrySerializer(serializers.ModelSerializer):
    subregion = serializers.CharField(source='subregion.name')

    class Meta:
        model = Country
        fields = ('id', 'name', 'subregion')


class ProjectThemeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectTheme
        fields = ('id', 'name')
        

class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    owner = UserPreviewSerializer()
    image = ImageSerializer(required=False)
    country = CountrySerializer()

    meta_data = MetaField(
        title='get_meta_title',
        fb_title='get_fb_title',
        description='pitch',
        keywords='tags',
        image_source='image',
        tweet='get_tweet',
    )

    def __init__(self, *args, **kwargs):
        super(ProjectSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = PROJECT_MODEL
        fields = ('id', 'created', 'title', 'pitch', 'description', 'owner',
                  'status', 'meta_data', 'image', 'country', 'theme')


class ProjectPreviewSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    image = SorlImageField('image', '400x300', crop='center')
    country = ProjectCountrySerializer(source='country')
    pitch = serializers.CharField(source='pitch')
    theme = ProjectThemeSerializer(source='theme')

    class Meta:
        model = PROJECT_MODEL


class ManageProjectSerializer(TaggableSerializerMixin, serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)

    url = serializers.HyperlinkedIdentityField(view_name='project_manage_detail')
    tags = TagSerializer()
    organization = serializers.PrimaryKeyRelatedField(
        source='organization', required=False)
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    editable = serializers.BooleanField(read_only=True)
    viewable = serializers.BooleanField(read_only=True)
    status = serializers.PrimaryKeyRelatedField(required=False)
    image = ImageSerializer(required=False)
    pitch = serializers.CharField(required=False)

    def validate_status(self, attrs, source):
        value = attrs.get(source, None)
        if not value:
            value = ProjectPhase.objects.order_by('sequence').all()[0]
        attrs[source] = value
        return attrs

    class Meta:
        model = PROJECT_MODEL
        exclude = ('owner', 'slug')
