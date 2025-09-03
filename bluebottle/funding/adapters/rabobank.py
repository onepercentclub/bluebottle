import requests
from django.conf import settings


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
        response = requests.post(
            self.iban_check_url,
            headers=headers,
            json=payload,
            cert=(self.public_cert, self.private_key),
            verify=True,
        )
        response.raise_for_status()
        return response.json()
