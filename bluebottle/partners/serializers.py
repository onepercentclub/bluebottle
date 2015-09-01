from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.projects.models import PartnerOrganization
from bluebottle.projects.serializers import ProjectPreviewSerializer
from rest_framework import serializers


class PartnerOrganizationPreviewSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)

    class Meta:
        model = PartnerOrganization
        fields = ('id', 'name', )


class PartnerOrganizationSerializer(PartnerOrganizationPreviewSerializer):
    projects = ProjectPreviewSerializer(source='projects')
    image = ImageSerializer(required=False)
    description = serializers.CharField(source='description')

    class Meta:
        model = PartnerOrganization
        fields = ('id', 'name', 'projects', 'description', 'image')

