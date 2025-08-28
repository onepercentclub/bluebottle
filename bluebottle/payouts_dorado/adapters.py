from builtins import str
from builtins import object
import json
import requests

from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from requests.exceptions import MissingSchema

from bluebottle.clients import properties
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.grant_management.models import GrantPayout


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
        payout_type = 'crowdfunding'
        if isinstance(self.payout, GrantPayout):
            payout_type = 'grant'

        # Send the signal to Dorado
        data = {
            'payout_id': self.payout.pk,
            'tenant': self.tenant.client_name,
            'payout_type': payout_type,
        }
        try:
            response = requests.post(self.settings['url'], data)
            response.raise_for_status()
        except requests.HTTPError:
            try:
                raise TransitionNotPossible(json.loads(response.content))
            except ValueError:
                raise TransitionNotPossible(response.content)
        except MissingSchema:
            raise ImproperlyConfigured("Incorrect Payout URL")
        except IOError as e:
            raise PayoutCreationError(str(e))
        except TypeError:
            raise ImproperlyConfigured("Invalid Payout settings")
