from builtins import object

from rest_framework import serializers

from bluebottle.offices.models import OfficeSubRegion, OfficeRegion


class SubregionSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = OfficeSubRegion
        fields = ('id', 'name', 'description', 'region')

    class JSONAPIMeta(object):
        resource_name = 'offices/subregions'
        included_resources = [
            'region'
        ]

    included_serializers = {
        'region': 'bluebottle.offices.serializers.RegionSerializer'
    }


class RegionSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = OfficeRegion
        fields = ('id', 'name', 'description')

    class JSONAPIMeta(object):
        resource_name = 'offices/regions'
