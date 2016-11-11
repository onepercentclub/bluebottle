import requests

from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from requests.exceptions import MissingSchema

from bluebottle.clients import properties


class DoradoPayoutAdapter(object):

    def __init__(self, project):
        self.settings = getattr(properties, 'PAYOUT_SERVICE', {})
        self.project = project
        self.tenant = connection.tenant

    def trigger_payout(self):
        # Send the signal to Dorado
        data = {
            'project': self.project.id,
            'tenant': self.tenant.schema_name
        }

        try:
            response = requests.post(self.settings['url'], data)
            if response.content != '{"status": "success"}':
                raise SystemError("Could not trigger payout")
        except MissingSchema:
            raise ImproperlyConfigured("Incorrect Payout URL")
