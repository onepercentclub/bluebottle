from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.utils.serializers import URLField

from bluebottle.utils.utils import get_organization_model, get_organizationdocument_model, get_organizationmember_model

ORGANIZATION_MODEL = get_organization_model()
MEMBER_MODEL = get_organizationmember_model()
DOCUMENT_MODEL = get_organizationdocument_model()

ORGANIZATION_FIELDS = ( 'id', 'name', 'slug', 'address_line1', 'address_line2', 'city', 'state', 'country', 
                       'postal_code', 'phone_number', 'website', 'email', 'twitter', 'facebook', 'skype', 'documents' )

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ORGANIZATION_MODEL
        fields = ORGANIZATION_FIELDS

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
        fields = ORGANIZATION_FIELDS + ( 'partner_organizations', 'created', 'updated' ) 
