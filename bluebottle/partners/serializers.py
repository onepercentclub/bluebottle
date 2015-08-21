from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.projects.models import PartnerOrganization
from bluebottle.projects.serializers import \
    ProjectPreviewSerializer as BaseProjectPreviewSerializer
from rest_framework import serializers


# This is a bit of a hack. We have an existing ProjectPreviewSerializer in /bb_projects/serializers.
# However, that serializer depends on properties calculated in the ProjectPreview view. Therefore, we
# cannot re-use the serializer. The serialzier below is the same, except it has the fields "people_requested"
# and "people_registered" removed.
from bluebottle.utils.serializer_dispatcher import get_serializer_class


class ProjectPreviewSerializer(BaseProjectPreviewSerializer):
    task_count = serializers.IntegerField(source='task_count')
    owner = get_serializer_class('AUTH_USER_MODEL', 'preview')(source='owner')
    partner = serializers.SlugRelatedField(slug_field='slug',
                                           source='partner_organization')
    is_funding = serializers.Field()

    class Meta(BaseProjectPreviewSerializer):
        model = BaseProjectPreviewSerializer.Meta.model
        fields = (
        'id', 'title', 'image', 'status', 'pitch', 'country', 'task_count',
        'allow_overfunding', 'latitude', 'longitude', 'is_campaign',
        'amount_asked', 'amount_donated', 'amount_needed', 'amount_extra',
        'deadline', 'status', 'owner', 'partner', 'is_funding')


class PartnerOrganizationPreviewSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)

    class Meta:
        model = PartnerOrganization
        fields = ('id', 'name',)


class PartnerOrganizationSerializer(PartnerOrganizationPreviewSerializer):
    projects = ProjectPreviewSerializer(source='projects')
    image = ImageSerializer(required=False)
    description = serializers.CharField(source='description')

    class Meta:
        model = PartnerOrganization
        fields = ('id', 'name', 'projects', 'description', 'image')
