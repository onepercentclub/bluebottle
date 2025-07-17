import base64
import requests
import time
from django.conf import settings


class RabobankAdapter:

    def __init__(self):

        self.public_cert = settings.RABOBANK["public_cert"]
        self.private_key = settings.RABOBANK["private_key"]
        self.cert_pass = settings.RABOBANK["cert_pass"]
        self.token_url = settings.RABOBANK["token_url"]
        self.client_id = settings.RABOBANK["client_id"]
        self.client_secret = settings.RABOBANK["client_secret"]
        self.api_key = settings.RABOBANK.get("api_key")  # Add API key

        self.iban_check_url = settings.RABOBANK["iban_check_url"]
        self.scope = 'surepay:ibannamecheck:read'

        self.access_token = None
        self.token_expiry = None
        self.refresh_token = None

    def _refresh_token_with_refresh_token(self):
        """
        Refresh access token using refresh token
        """
        if not self.refresh_token:
            raise Exception("No refresh token available")

        cert_path, key_path = self._create_cert_files()

        try:
            # Create Basic auth header
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            auth_header = f"Basic {encoded_credentials}"

            response = requests.post(
                "https://oauth-sandbox.rabobank.nl/openapi/sandbox/oauth2-premium/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                },
                cert=(self.public_cert, self.private_key),
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                verify=False,
            )

            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Response body: {response.text}")

            response.raise_for_status()
            data = response.json()
            print(f"Response data token: {data}")

            self.access_token = data["access_token"]
            self.token_expiry = int(time.time()) + int(data.get("expires_in", 1800))
            self.refresh_token = data.get("refresh_token", self.refresh_token)

            return data
        finally:
            self._cleanup_cert_files(cert_path, key_path)

    def _refresh_token(self):

        print(f"Making request to: {self.token_url}")
        print(f"Client ID: {self.client_id}")
        print(f"Scope: {self.scope}")

        # Create Basic auth header
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        auth_header = f"Basic {encoded_credentials}"

        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "scope": self.scope,
            },
            cert=(self.public_cert, self.private_key),
            headers={
                "Authorization": auth_header,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            verify=True,
        )

        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response body: {response.text}")

        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        self.token_expiry = int(time.time()) + int(data.get("expires_in", 1800))

    def _get_token(self):
        if not self.access_token or (self.token_expiry and time.time() > self.token_expiry - 60):
            if self.refresh_token:
                self._refresh_token_with_refresh_token()
            else:
                self._refresh_token()
        return self.access_token

    def check_iban_name(self, iban, name):

        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

        # Add API key if available
        if self.api_key:
            headers["API-Key"] = self.api_key

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
