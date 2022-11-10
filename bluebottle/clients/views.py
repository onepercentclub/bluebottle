# -*- coding: utf-8 -*-

from rest_framework import views, response
from django.db import connection

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

        member_settings = obj['platform']['members']
        if member_settings['closed'] and not request.user.is_authenticated:
            obj = {
                'tenant': connection.tenant.client_name,
                'platform': {
                    'members': {
                        'closed': member_settings['closed'],
                        'background': member_settings['background'],
                        'login_methods': member_settings['login_methods'],
                        'session_only': member_settings['session_only'],
                        'email_domain': member_settings['email_domain'],
                        'confirm_signup': member_settings['confirm_signup'],
                    }
                }
            }

        return response.Response(obj)
