# -*- coding: utf-8 -*-

from rest_framework import views, response
from django.db import connection
from django.views.generic import TemplateView


from bluebottle.clients.utils import get_public_properties


class Robots(TemplateView):
    template_name = 'robots.txt'


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
        content_settings = obj['platform']['content']
        languages = obj['languages']
        if member_settings['closed'] and not request.user.is_authenticated:
            obj = {
                'tenant': connection.tenant.client_name,
                'languages': languages,
                'platform': {
                    'content': content_settings,
                    'members': {
                        'closed': member_settings['closed'],
                        'background': member_settings['background'],
                        'login_methods': member_settings['login_methods'],
                        'session_only': member_settings['session_only'],
                        'email_domain': member_settings['email_domain'],
                        'confirm_signup': member_settings['confirm_signup'],
                        'consent_link': member_settings['consent_link'],
                    }
                }
            }

        return response.Response(obj)
