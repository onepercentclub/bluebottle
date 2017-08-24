from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.organizations.models import Organization, OrganizationContact
from bluebottle.utils.serializers import URLField


class OrganizationPreviewSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_null=True)
    name = serializers.CharField(required=True)
    website = URLField(required=False, allow_blank=True)
    logo = ImageSerializer(required=False, allow_null=True)

    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug', 'website', 'logo')


class OrganizationSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_null=True)
    name = serializers.CharField(required=True)
    website = URLField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    contacts = serializers.SerializerMethodField()
    logo = ImageSerializer(required=False, allow_null=True)

    def get_contacts(self, obj):
        owner = self.context['request'].user

        try:
            contacts = OrganizationContact.objects.filter(owner=owner, organization=obj).order_by('-created')
        except TypeError:
            contacts = []

        return OrganizationContactSerializer(contacts, many=True, required=True).to_representation(contacts)

    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug', 'address_line1', 'address_line2',
                  'city', 'state', 'country', 'postal_code', 'phone_number',
                  'website', 'email', 'contacts', 'partner_organizations',
                  'created', 'updated', 'logo')


class OrganizationContactSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    organization = serializers.PrimaryKeyRelatedField(required=True, queryset=Organization.objects)

    class Meta:
        model = OrganizationContact
        fields = ('name', 'email', 'phone', 'owner', 'organization', 'id')
