from builtins import object

from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.offices.models import OfficeSubRegion, OfficeRegion


class SubregionSerializer(ModelSerializer):

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


class RegionSerializer(ModelSerializer):

    class Meta(object):
        model = OfficeRegion
        fields = ('id', 'name', 'description')

    class JSONAPIMeta(object):
        resource_name = 'offices/regions'
