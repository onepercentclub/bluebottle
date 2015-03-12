from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.utils.model_dispatcher import (get_organization_model,
                                               get_organizationdocument_model,
                                               get_organizationmember_model)
from bluebottle.utils.serializers import URLField
from django_iban.validators import iban_validator, swift_bic_validator
from rest_framework import serializers

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
        fields = ('id', 'organization', 'file')


class ManageOrganizationSerializer(OrganizationSerializer):
    slug = serializers.SlugField(required=False)

    documents = OrganizationDocumentSerializer(many=True, source='documents', read_only=True)

    name = serializers.CharField(required=True)
    website = URLField(required=False)
    email = serializers.EmailField(required=False)
    twitter = serializers.CharField(required=False)
    facebook = serializers.CharField(required=False)
    skype = serializers.CharField(required=False)

    def validate_account_iban(self, attrs, source):
        value = attrs[source]
        if value:
            iban_validator(value)
        return attrs

    def validate_account_bic(self, attrs, source):
        value = attrs[source]
        if value:
            swift_bic_validator(value)
        return attrs

    class Meta:
        model = ORGANIZATION_MODEL
        fields = ORGANIZATION_FIELDS + ( 'account_holder_name', 'account_holder_address', 'account_holder_postal_code', 
                    'account_holder_city', 'account_holder_country', 'account_iban', 'account_bic', 'account_number', 'account_bank_name',
                    'account_bank_address', 'account_bank_postal_code', 'account_bank_city', 'account_bank_country', 'account_other',
                    'partner_organizations', 'created', 'updated' ) 
