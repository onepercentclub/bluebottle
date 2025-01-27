from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.redirects.models import Redirect


class RedirectSerializer(ModelSerializer):

    class Meta:
        model = Redirect
        fields = ('id', 'old_path', 'new_path')

    class JSONAPIMeta:
        resource_name = 'redirects'
