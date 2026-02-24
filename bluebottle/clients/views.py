# -*- coding: utf-8 -*-

from django.db import connection
from django.views.generic import TemplateView
from rest_framework import views, response

from bluebottle.clients.utils import get_public_properties
from bluebottle.members.models import MemberPlatformSettings


class Robots(TemplateView):
    template_name = 'robots.txt'

    def get_context_data(self, **kwargs):
        return dict(settings=MemberPlatformSettings.load(), **super().get_context_data(**kwargs))


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

        is_jwt_authenticated = (
            request.user.is_authenticated
            and request.META.get('HTTP_AUTHORIZATION', '').startswith('JWT ')
        )

        if member_settings['closed'] and not is_jwt_authenticated:
            obj = {
                'siteName': obj['siteName'],
                'tenant': connection.tenant.client_name,
                'languages': languages,
                'platform': {
                    'content': content_settings,
                    'members': {
                        'closed': member_settings['closed'],
                        'background': member_settings['background'],
                        'login_methods': member_settings['login_methods'],
                        'session_only': member_settings['session_only'],
                        'email_domains': member_settings['email_domains'],
                        'confirm_signup': member_settings['confirm_signup'],
                        'consent_link': member_settings['consent_link'],
                        'request_access_method': member_settings['request_access_method'],
                        'request_access_instructions': member_settings['request_access_instructions'],
                        'request_access_email': member_settings['request_access_email'],
                    }
                }
            }

        return response.Response(obj)
