from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.utils.serializers import URLField

from . import get_organization_model
from .models import OrganizationDocument


ORGANIZATION_MODEL = get_organization_model()


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = ORGANIZATION_MODEL
        exclude = ('deleted',)


class OrganizationDocumentSerializer(serializers.ModelSerializer):

    file = PrivateFileSerializer()

    class Meta:
        model = OrganizationDocument
        fields = ('id', 'organization', 'file')


class ManageOrganizationSerializer(OrganizationSerializer):

    slug = serializers.SlugField(required=False)

    documents = OrganizationDocumentSerializer(many=True, source='organizationdocument_set', required=False)

    name = serializers.CharField(required=True)
    description = serializers.CharField(required=False)
    website = URLField(required=False)
    email = serializers.EmailField(required=False)
    twitter = serializers.CharField(required=False)
    facebook = serializers.CharField(required=False)
    skype = serializers.CharField(required=False)
    legal_status = serializers.CharField(required=False)

    class Meta:
        model = ORGANIZATION_MODEL
        exclude = ('deleted',)
