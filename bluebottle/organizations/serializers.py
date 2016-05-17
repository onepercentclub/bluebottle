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
    slug = serializers.SlugField(required=False)
    name = serializers.CharField(required=True)
    website = URLField(required=False)
    email = serializers.EmailField(required=False)

    class Meta:
        model = Organization
        fields = OrganizationSerializer.Meta.fields + ('partner_organizations',
                                                       'created', 'updated')
