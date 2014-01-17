from rest_framework import serializers

from bluebottle.accounts.serializers import UserPreviewSerializer
from bluebottle.bluebottle_drf2.serializers import (
    SorlImageField, EuroField, TagSerializer, ImageSerializer, OEmbedField,
    TaggableSerializerMixin)
from bluebottle.geo.models import Country
from bluebottle.projects.models import (
    Project, ProjectTheme, ProjectBudgetLine, ProjectDetailField,
    ProjectDetailFieldAttribute, ProjectDetailFieldValue, ProjectDetail, ProjectPhase)
from bluebottle.utils.serializers import MetaField


class ProjectPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase


class ProjectCountrySerializer(serializers.ModelSerializer):
    subregion = serializers.CharField(source='subregion.name')

    class Meta:
        model = Country
        fields = ('id', 'name', 'subregion')


class ProjectDetailSerializer(serializers.ModelSerializer):

    field = serializers.CharField(source='field.slug', read_only=True)

    class Meta:
        model = ProjectDetail
        fields = ('field', 'value')


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
        fields = ('id', 'created', 'title', 'pitch', 'description', 'owner',
                  'status', 'meta_data', 'image')


class ProjectPreviewSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    image = SorlImageField('image', '400x300', crop='center')
    country = ProjectCountrySerializer(source='country')
    pitch = serializers.CharField(source='pitch')

    class Meta:
        model = Project
        fields = ('id', 'title', 'image', 'status', 'country')


class ManageProjectSerializer(TaggableSerializerMixin, serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)

    url = serializers.HyperlinkedIdentityField(view_name='project_manage_detail')
    tags = TagSerializer()
    organization = serializers.PrimaryKeyRelatedField(
        source='organization', required=False)
    video_html = OEmbedField(source='video_url', maxwidth='560', maxheight='315')
    editable = serializers.BooleanField(read_only=True)
    viewable = serializers.BooleanField(read_only=True)
    status = serializers.PrimaryKeyRelatedField()
    image = ImageSerializer(required=False)

    pitch = serializers.CharField(required=False)

    class Meta:
        model = Project
        exclude = ('owner', 'slug')


class ProjectThemeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectTheme
        fields = ('id', 'name')
        
        
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
    id = serializers.CharField(source='slug', read_only=True)
    options = ProjectDetailFieldValueSerializer(many=True, source='projectdetailfieldvalue_set')
    attributes = ProjectDetailFieldAttributeSerializer(many=True, source='projectdetailfieldattribute_set')

    class Meta:
        model = ProjectDetailField
        fields = ('id', 'name', 'description', 'type', 'options', 'attributes')

