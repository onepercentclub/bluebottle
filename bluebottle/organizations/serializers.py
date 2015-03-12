from bluebottle.bb_organizations.serializers import \
    ManageOrganizationSerializer as BaseManageOrganizationSerializer
from bluebottle.bb_organizations.serializers import \
    OrganizationSerializer as BaseOrganizationSerializer
from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.utils.serializers import AddressSerializer, URLField
from rest_framework import serializers

from .models import Organization, OrganizationDocument


class OrganizationSerializer(BaseOrganizationSerializer):

    class Meta(BaseOrganizationSerializer):
        model = BaseOrganizationSerializer.Meta.model
        fields = BaseOrganizationSerializer.Meta.fields


class OrganizationDocumentSerializer(serializers.ModelSerializer):

    file = PrivateFileSerializer()

    class Meta:
        model = OrganizationDocument
        fields = ('id', 'organization', 'file')


class ManageOrganizationSerializer(BaseManageOrganizationSerializer):

    slug = serializers.SlugField(required=False)

    class Meta(BaseManageOrganizationSerializer):
        model = BaseManageOrganizationSerializer.Meta.model
        fields = BaseManageOrganizationSerializer.Meta.fields
