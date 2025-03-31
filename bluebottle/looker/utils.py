from future import standard_library

from bluebottle.members.models import MemberPlatformSettings

standard_library.install_aliases()
import base64
import binascii
import hmac
import json
import os
import time
from builtins import object
from collections import OrderedDict
from hashlib import sha1
from urllib.parse import quote_plus, urlencode

from django.conf import settings
from django.db import connection

from bluebottle.analytics.models import AnalyticsPlatformSettings
from bluebottle.clients import properties
from bluebottle.utils.utils import get_current_host


class LookerSSOEmbed(object):
    session_length = settings.LOOKER_SESSION_LENGTH
    models = ('Projects', )
    permissions = ('see_user_dashboards', 'see_lookml_dashboards', 'access_data', 'see_looks', )

    def __init__(self, user, type, id, hide_filters=None):
        if not hide_filters:
            hide_filters = []
        self.user = user
        self._path = '/embed/{}s/{}'.format(type, id)
        hide_filters = "&".join([f'hide_filter={filter}' for filter in hide_filters])
        self._path += '?' + hide_filters

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
        signer = hmac.new(
            settings.LOOKER_SECRET.encode('utf-8'), string_to_sign.encode('utf-8').strip(), sha1
        )
        return base64.b64encode(signer.digest()).strip()

    @property
    def url(self):
        schema_name = connection.tenant.schema_name
        analytics_settings = AnalyticsPlatformSettings.objects.get()
        member_settings = MemberPlatformSettings.objects.get()

        subregions = list(self.user.subregion_manager.values_list('id', flat=True))
        subregions = ";".join(map(str, subregions))

        params = OrderedDict([
            ('nonce', self.nonce.decode()),
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
            ('user_attributes', {
                'tenant': schema_name,
                'fiscal_month_offset': member_settings.fiscal_month_offset,
                'user_base': analytics_settings.user_base,
                'language': properties.LANGUAGE_CODE,
                'region_manager': subregions,
            }),
            ('force_logout_login', True),
        ])
        json_params = OrderedDict((key, json.dumps(value)) for key, value in list(params.items()))

        json_params['signature'] = self.sign(json_params)

        return '{}{}?{}'.format(
            'https://' + self.looker_host, self.path, urlencode(json_params)
        )
