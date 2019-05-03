from rest_framework import serializers

from bluebottle.organizations.models import Organization, OrganizationContact

from rest_framework_json_api.serializers import ModelSerializer


class OrganizationSerializer(ModelSerializer):
    description = serializers.CharField(required=False, allow_blank=True)
    slug = serializers.SlugField(allow_null=True, required=False)
    name = serializers.CharField(required=True)
    website = serializers.CharField(allow_blank=True, required=False)

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta:
        model = Organization
        fields = (
            'id', 'name', 'slug', 'description', 'website', 'owner',
        )

        meta_fields = ['created', 'updated']

    class JSONAPIMeta:
        resource_name = 'organizations'
        included_resources = ['owner', ]


class OrganizationContactSerializer(ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta:
        model = OrganizationContact
        fields = (
            'id', 'name', 'email', 'phone',
        )

        meta_fields = ['created', 'updated']

    class JSONAPIMeta:
        resource_name = 'organization-contacts'
        included_resources = ['owner', ]
