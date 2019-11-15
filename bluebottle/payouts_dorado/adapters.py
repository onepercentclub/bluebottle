import json
import requests

from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from requests.exceptions import MissingSchema

from bluebottle.clients import properties


class PayoutValidationError(Exception):
    pass


class PayoutCreationError(Exception):
    pass


class DoradoPayoutAdapter(object):

    def __init__(self, payout):
        self.settings = getattr(properties, 'PAYOUT_SERVICE', None)
        self.payout = payout
        self.tenant = connection.tenant

    def trigger_payout(self):
        # Send the signal to Dorado
        data = {
            'payout_id': self.payout.pk,
            'tenant': self.tenant.client_name,
        }

        try:
            response = requests.post(self.settings['url'], data)
            response.raise_for_status()
        except requests.HTTPError:
            try:
                raise PayoutValidationError(json.loads(response.content))
            except ValueError:
                raise PayoutCreationError(response.content)
        except MissingSchema:
            raise ImproperlyConfigured("Incorrect Payout URL")
        except IOError, e:
            raise PayoutCreationError(unicode(e))
        except TypeError:
            raise ImproperlyConfigured("Invalid Payout settings")
