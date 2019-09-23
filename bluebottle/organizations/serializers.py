from rest_framework import serializers

from bluebottle.organizations.models import Organization, OrganizationContact

from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.utils.fields import ValidationErrorsField, RequiredErrorsField
from bluebottle.utils.serializers import NoCommitMixin


class OrganizationSerializer(NoCommitMixin, ModelSerializer):
    description = serializers.CharField(required=False, allow_blank=True)
    slug = serializers.SlugField(allow_null=True, required=False)
    name = serializers.CharField(required=True)
    website = serializers.CharField(allow_blank=True, required=False)

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta:
        model = Organization
        fields = (
            'id', 'name', 'slug', 'description', 'website', 'owner',
            'required', 'errors',
        )

        meta_fields = ['created', 'updated', 'errors', 'required']

    class JSONAPIMeta:
        resource_name = 'organizations'
        included_resources = ['owner', ]


class OrganizationContactSerializer(NoCommitMixin, ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    email = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta:
        model = OrganizationContact
        fields = (
            'id', 'name', 'email', 'phone',
            'required', 'errors',
        )

        meta_fields = ['created', 'updated', 'errors', 'required']

    class JSONAPIMeta:
        resource_name = 'organization-contacts'
        included_resources = ['owner', ]
