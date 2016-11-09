import requests
import urllib

from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from requests.exceptions import MissingSchema

from bluebottle.clients import properties
from bluebottle.payouts_dorado.models import Payout


class DoradoPayoutAdapter(object):

    def __init__(self, project):
        self.settings = getattr(properties, 'PAYOUT_SERVICE', {})
        self.project = project
        self.tenant = connection.tenant

    def trigger_payout(self):
        # Generate local Payout objects
        for total in self.project.totals_donated:
            Payout.objects.create(project=self.project, amount=total)

        # Send the signal to Dorado
        data = {
            'project': self.project.id,
            'tenant': self.tenant.schema_name
        }

        url = self.settings['url'] + urllib.urlencode(data)
        try:
            response = requests.get(url)
            if response.content != '{"status": "success"}':
                raise SystemError("Could not trigger payout")
        except MissingSchema:
            raise ImproperlyConfigured("Incorrect Payout URL")
