import binascii
from collections import OrderedDict
import json
import hmac
import base64
from hashlib import sha1
import time
import os
from urllib import urlencode, quote_plus
from urlparse import urljoin

from django.db import connection
from django.conf import settings
from django.views.generic.base import TemplateView

from bluebottle.utils.utils import get_current_host


class LookerEmbed(object):
    session_length = 60 * 10
    models = ('First', )
    permissions = ('see_user_dashboards', 'see_lookml_dashboards', 'access_data', 'see_looks', )

    def __init__(self, user, path):
        self.user = user
        self._path = path

    @property
    def path(self):
        return '/login/embed/{}'.format(quote_plus(self._path))

    @property
    def nonce(self):
        return binascii.hexlify(os.urandom(16))

    @property
    def time(self):
        return int(time.time())

    @property
    def looker_host(self):
        if hasattr(settings, 'LOOKER_HOST'):
            return settings.LOOKER_HOST
        else:
            return 'looker.{}'.format(
                get_current_host(False)
            )

    def sign(self, params):
        attrs = (
            'looker_host', 'path', 'nonce', 'time', 'session_length', 'external_user_id',
            'permissions', 'models', 'group_ids', 'external_group_id', 'user_attributes',
            'access_filters'
        )

        values = [params.get(attr, getattr(self, attr, None)) for attr in attrs]
        values = [value for value in values if value is not None]

        string_to_sign = "\n".join(values)
        print string_to_sign
        signer = hmac.new(
            settings.LOOKER_SECRET, string_to_sign.encode('utf-8').strip(), sha1
        )
        return base64.b64encode(signer.digest()).strip()

    @property
    def url(self):
        schema_name = connection.tenant.schema_name
        params = OrderedDict([
            ('nonce', self.nonce),
            ('time', self.time),
            ('session_length', self.session_length),
            ('external_user_id', '{}-{}'.format(schema_name, self.user.id)),
            ('permissions', self.permissions),
            ('models', self.models),
            ('access_filters', {}),
            ('first_name', self.user.first_name),
            ('last_name', self.user.last_name),
            ('group_ids', [3]),
            ('external_group_id', 'Back-office Users'),
            ('user_attributes', {'tenant': schema_name}),
            ('force_logout_login', True),
        ])
        json_params = OrderedDict((key, json.dumps(value)) for key, value in params.items())

        json_params['signature'] = self.sign(json_params)
        print json_params['signature']

        return '{}{}?{}'.format(
            'https://' + self.looker_host, self.path, urlencode(json_params)
        )


class AnalyticsView(TemplateView):

    template_name = 'analytics/index.html'

    mapping = {
        'users': 16,
        'projects': 18,

        'volunteers': 19,
        'tasks': 21,
        'hours': 20,

        'donations': 17,
        'supporters': 22,

        'voting': 16,

    }

    def get_context_data(self, **kwargs):
        context = super(AnalyticsView, self).get_context_data(**kwargs)
        # We need this so 'View Site' shows in admin menu
        context['looker_embed_url'] = LookerEmbed(self.request.user, '/embed/dashboards/3').url
        print context['looker_embed_url']
        return context
