# -*- coding: utf-8 -*-

from rest_framework import views, response

from bluebottle.clients.utils import get_public_properties


class SettingsView(views.APIView):
    """
    Return the tenant settings as a json object
    """
    permission_classes = ()

    def get(self, request, format=None):
        """
        Return settings
        """
        obj = get_public_properties(request)
        if obj['platform']['members']['closed'] and not request.user.is_authenticated:
            obj = {
                'platform': {'members': {'closed': True}}
            }

        return response.Response(obj)
