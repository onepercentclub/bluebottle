import json
from rest_framework import views, response
from bluebottle.utils.context_processors import tenant_properties


class SettingsView(views.APIView):
    """
    Return the tenant settings as a json object
    """

    def get(self, request, format=None):
        """
        Return settings
        """
        obj = tenant_properties(request)
        return response.Response(json.loads(obj['settings']))