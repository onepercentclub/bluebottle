from django.core.exceptions import ImproperlyConfigured
from django.db import connection

from bluebottle.clients import properties
from .utils import process_payout


class DoradoPayoutAdapter(object):

    def __init__(self, project):
        self.settings = getattr(properties, 'PAYOUT_SERVICE', None)
        self.project = project
        self.tenant = connection.tenant

    def trigger_payout(self):
        # Send the signal to Dorado
        data = {
            'project_id': self.project.id,
            'tenant': self.tenant.schema_name
        }

        try:
            process_payout(self.settings['url'], data)
        except TypeError:
            raise ImproperlyConfigured("Invalid Payout settings")
