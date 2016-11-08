import requests
import urllib

from django.core.exceptions import ImproperlyConfigured
from django.db import connection

from bluebottle.clients import properties


class DoradoPayoutAdapter(object):

    def __init__(self, project):
        self.settings = getattr(properties, 'PAYOUT_SERVICE', False)
        self.project = project
        self.tenant = connection.tenant

    def trigger_payout(self):
        if self.settings.url[-1:] != '/':
            raise ImproperlyConfigured('PAYOUT_SERVICE.url should and with a slash')
        data = {
            'project': self.project.id,
            'tenant': self.tenant.schema_name
        }
        url = self.settings.url + urllib.urlencode(data)
        response = requests.get(url)
        if response.data != '{"status": "success"}':
            raise SystemError("Could not trigger payout")
