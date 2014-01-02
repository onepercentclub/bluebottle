from bluebottle.projects.models import ProjectBudgetLine, ProjectDetailField, ProjectDetailFieldAttribute, ProjectDetailFieldValue
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from bluebottle.accounts.serializers import UserPreviewSerializer
from bluebottle.bluebottle_drf2.serializers import (
    SorlImageField, EuroField, TagSerializer, ImageSerializer, OEmbedField,
    TaggableSerializerMixin)
from bluebottle.geo.models import Country
from bluebottle.utils.serializers import MetaField
from bluebottle.projects.models import Project, ProjectTheme, ProjectBudgetLine


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
        model = Project
        depth = 1
        fields = ('id', 'created', 'title', 'pitch', 'description', 'owner',
                  'phase', 'meta_data', 'image', 'details')


class ProjectPreviewSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    image = SorlImageField('image', '400x300', crop='center')
    country = ProjectCountrySerializer(source='country')
    pitch = serializers.CharField(source='pitch')

    class Meta:
        model = Project
        fields = ('id', 'title', 'image', 'phase', 'country')


class ManageProjectSerializer(TaggableSerializerMixin, serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)

    url = serializers.HyperlinkedIdentityField(view_name='project-manage-detail')
    phase = serializers.CharField(read_only=True)
    tags = TagSerializer()
    organization = serializers.PrimaryKeyRelatedField(source='organization', required=False)
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    editable = serializers.BooleanField(read_only=True)

    image = ImageSerializer(required=False)

    class Meta:
        model = Project
        fields = ('id', 'created', 'title', 'url', 'phase', 'image', 'pitch',
                  'tags', 'description', 'country', 'latitude', 'longitude',
                  'reach', 'organization', 'image', 'video_html', 'video_url',
                  'money_needed', 'editable')


class ProjectThemeSerializer(serializers.ModelSerializer):
    title = serializers.Field(source='name')

    class Meta:
        model = ProjectTheme
        fields = ('id', 'title')
        
        
class ProjectBudgetLineSerializer(serializers.ModelSerializer):

    amount = EuroField()
    project = serializers.SlugRelatedField(slug_field='slug')

    class Meta:
        model = ProjectBudgetLine
        fields = ('id', 'project', 'description', 'amount')

class ProjectDetailFieldAttributeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectDetailFieldAttribute
        fields = ('id', 'attribute', 'value')

class ProjectDetailFieldValueSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectDetailFieldValue
        fields = ('id', 'value', 'text')


class ProjectDetailFieldSerializer(serializers.ModelSerializer):

    options = ProjectDetailFieldValueSerializer(many=True, source='projectdetailfieldvalue_set')
    attributes = ProjectDetailFieldAttributeSerializer(many=True, source='projectdetailfieldattribute_set')

    class Meta:
        model = ProjectDetailField
        fields = ('id', 'name', 'description', 'type', 'options', 'attributes')

