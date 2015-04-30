from rest_framework import serializers

from bluebottle.utils.serializers import AddressSerializer, URLField

from .models import Organization

from bluebottle.bb_organizations.serializers import (OrganizationSerializer as BaseOrganizationSerializer,
                                                     ManageOrganizationSerializer as BaseManageOrganizationSerializer)


class OrganizationSerializer(BaseOrganizationSerializer):

    class Meta(BaseOrganizationSerializer):
        model = BaseOrganizationSerializer.Meta.model
        fields = BaseOrganizationSerializer.Meta.fields


class ManageOrganizationSerializer(BaseManageOrganizationSerializer):

    slug = serializers.SlugField(required=False)

    class Meta(BaseManageOrganizationSerializer):
        model = BaseManageOrganizationSerializer.Meta.model
        fields = BaseManageOrganizationSerializer.Meta.fields

