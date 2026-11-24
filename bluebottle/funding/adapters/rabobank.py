import logging

import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class IbanCheckError(Exception):
    """The IBAN check service could not process the request."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RabobankAdapter:

    def __init__(self):

        self.public_cert = settings.RABOBANK["public_cert"]
        self.private_key = settings.RABOBANK["private_key"]
        self.client_id = settings.RABOBANK["client_id"]
        self.client_secret = settings.RABOBANK["client_secret"]
        self.iban_check_url = settings.RABOBANK["iban_check_url"]
        self.scope = 'surepay:ibannamecheck:read'

    def check_iban_name(self, iban, name):

        headers = {
            "X-IBM-Client-Id": self.client_id,
            "Content-Type": "application/json",
        }

        payload = {"accountId": {"value": iban, "type": "IBAN"}, "name": name}
        try:
            response = requests.post(
                self.iban_check_url,
                headers=headers,
                json=payload,
                cert=(self.public_cert, self.private_key),
                verify=True,
            )
            response.raise_for_status()
        except requests.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            body = error.response.text[:1000] if error.response is not None else ''
            logger.error(
                'Rabobank IBAN check failed: status=%s iban=%s...%s body=%s',
                status_code, iban[:4], iban[-4:], body
            )
            if status_code == 400:
                message = _(
                    'The bank could not check this account. '
                    'Please verify the IBAN and the account holder name and try again.'
                )
            else:
                message = _(
                    'The bank account check is temporarily unavailable. Please try again later.'
                )
            raise IbanCheckError(message, status_code)
        except requests.RequestException as error:
            logger.error('Rabobank IBAN check request failed: %r', error)
            raise IbanCheckError(
                _('The bank account check is temporarily unavailable. Please try again later.')
            )
        return response.json()
