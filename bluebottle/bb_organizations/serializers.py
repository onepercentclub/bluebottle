from rest_framework import serializers

from bluebottle.utils.model_dispatcher import get_organization_model, get_organizationmember_model

ORGANIZATION_MODEL = get_organization_model()
MEMBER_MODEL = get_organizationmember_model()


ORGANIZATION_FIELDS = ( 'id', 'name', 'slug', 'address_line1', 'address_line2',
                        'city', 'state', 'country', 'postal_code', 'phone_number',
                        'email')


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ORGANIZATION_MODEL
        fields = ORGANIZATION_FIELDS


class ManageOrganizationSerializer(OrganizationSerializer):
    slug = serializers.SlugField(required=False)

    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=False)

    class Meta:
        model = ORGANIZATION_MODEL
        fields = ORGANIZATION_FIELDS + ('partner_organizations',
                                        'created', 'updated')
