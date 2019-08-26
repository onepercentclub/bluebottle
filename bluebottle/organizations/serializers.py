from rest_framework import serializers

from bluebottle.organizations.models import Organization, OrganizationContact

from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.utils.serializers import (
    NonModelRelatedResourceField, ValidationSerializer, NoCommitMixin
)


class OrganizationValidationSerializer(ValidationSerializer):
    name = serializers.CharField()
    website = serializers.CharField()

    class Meta:
        model = Organization
        fields = (
            'name', 'website', )

    class JSONAPIMeta:
        resource_name = 'organization-validations'


class OrganizationContactValidationSerializer(ValidationSerializer):
    name = serializers.CharField()
    email = serializers.CharField()

    class Meta:
        model = OrganizationContact
        fields = (
            'name', 'email',
        )

    class JSONAPIMeta:
        resource_name = 'organization-contact-validations'


class OrganizationSerializer(NoCommitMixin, ModelSerializer):
    description = serializers.CharField(required=False, allow_blank=True)
    slug = serializers.SlugField(allow_null=True, required=False)
    name = serializers.CharField(required=True)
    website = serializers.CharField(allow_blank=True, required=False)

    validations = NonModelRelatedResourceField(OrganizationValidationSerializer)

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'validations': 'bluebottle.organizations.serializers.OrganizationValidationSerializer',
    }

    class Meta:
        model = Organization
        fields = (
            'id', 'name', 'slug', 'description', 'website', 'owner', 'validations',
        )

        meta_fields = ['created', 'updated']

    class JSONAPIMeta:
        resource_name = 'organizations'
        included_resources = ['owner', 'validations']


class OrganizationContactSerializer(NoCommitMixin, ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    email = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    validations = NonModelRelatedResourceField(OrganizationContactValidationSerializer)

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'validations': 'bluebottle.organizations.serializers.OrganizationContactValidationSerializer',
    }

    class Meta:
        model = OrganizationContact
        fields = (
            'id', 'name', 'email', 'phone', 'validations',
        )

        meta_fields = ['created', 'updated']

    class JSONAPIMeta:
        resource_name = 'organization-contacts'
        included_resources = ['owner', 'validations']
