import requests
import time
from django.conf import settings


class AbnAmroAdapter:

    def __init__(self):

        self.client_id = settings.IBAN_CHECK_API['client_id']
        self.public_cert = settings.IBAN_CHECK_API['public_cert']
        self.private_key = settings.IBAN_CHECK_API['private_key']
        self.token_url = settings.IBAN_CHECK_API['token_url']
        self.api_key = settings.IBAN_CHECK_API['api_key']

        self.base_url = settings.IBAN_CHECK_API['base_url']
        self.scope = 'surepay:ibannamecheck:read'

        self.access_token = None
        self.token_expiry = None

    def _refresh_token(self):
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "scope": self.scope
            },
            cert=(self.public_cert, self.private_key),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        self.token_expiry = int(time.time()) + int(data.get("expires_in", 1800))

    def _get_token(self):
        if not self.access_token or (self.token_expiry and time.time() > self.token_expiry - 60):
            self._refresh_token()
        return self.access_token

    def check_iban_name(self, iban, name):

        url = f"{self.base_url}/third-party-api/surepay/iban-name-check/v3"
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "accountId": {
                "value": iban,
                "type": "IBAN"
            },
            "name": name
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
