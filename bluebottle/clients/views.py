# -*- coding: utf-8 -*-
import time

from django.utils.http import http_date

from rest_framework import views, response

from bluebottle.clients.utils import get_public_properties
from bluebottle.utils.views import ExpiresMixin


class SettingsView(ExpiresMixin, views.APIView):
    """
    Return the tenant settings as a json object
    """
    permission_classes = ()

    def get(self, request, format=None):
        """
        Return settings
        """
        obj = get_public_properties(request)
        resp = response.Response(obj)
        resp['Expires'] = http_date(time.time() + 300)
        return resp
