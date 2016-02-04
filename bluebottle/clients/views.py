import json
from rest_framework import generics
from bluebottle.clients.serializers import SettingsSerializer
from bluebottle.utils.context_processors import tenant_properties


class SettingsView(generics.RetrieveAPIView):
    """
    Return the tenant settings as a json object
    """
    serializer_class = SettingsSerializer

    def get_object(self):
        obj = tenant_properties(self.request)
        return {'id': 'settings', 'settings': json.loads(obj['settings'])}