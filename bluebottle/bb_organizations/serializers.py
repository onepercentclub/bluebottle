from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.utils.serializers import URLField

from . import get_organization_model, get_organizationdocument_model, get_organizationmember_model

ORGANIZATION_MODEL = get_organization_model()
MEMBER_MODEL = get_organizationmember_model()
DOCUMENT_MODEL = get_organizationdocument_model()


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ORGANIZATION_MODEL
        exclude = ('deleted',)


class OrganizationDocumentSerializer(serializers.ModelSerializer):
    file = PrivateFileSerializer()

    class Meta:
        model = DOCUMENT_MODEL


class ManageOrganizationSerializer(OrganizationSerializer):
    slug = serializers.SlugField(required=False)

    documents = OrganizationDocumentSerializer(many=True, source='documents', read_only=True)

    name = serializers.CharField(required=True)
    website = URLField(required=False)
    email = serializers.EmailField(required=False)
    twitter = serializers.CharField(required=False)
    facebook = serializers.CharField(required=False)
    skype = serializers.CharField(required=False)

    class Meta:
        model = ORGANIZATION_MODEL
        exclude = ('deleted', )
