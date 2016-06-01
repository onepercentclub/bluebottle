from rest_framework import serializers

from bluebottle.organizations.models import Organization
from bluebottle.utils.serializers import URLField


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug', 'address_line1', 'address_line2',
                  'city', 'state', 'country', 'postal_code', 'phone_number',
                  'website', 'email')


class ManageOrganizationSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_null=True)
    name = serializers.CharField(required=True, allow_blank=True)
    website = URLField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = Organization
        fields = OrganizationSerializer.Meta.fields + ('partner_organizations',
                                                       'created', 'updated')
