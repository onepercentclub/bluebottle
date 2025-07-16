import base64
import os
import tempfile
import time

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from django.conf import settings


class RabobankAdapter:

    def __init__(self):

        self.public_cert = settings.RABOBANK["public_cert"]
        self.private_key = settings.RABOBANK["private_key"]
        self.cert_pass = settings.RABOBANK["cert_pass"]
        self.token_url = settings.RABOBANK["token_url"]
        self.client_id = settings.RABOBANK["client_id"]
        self.client_secret = settings.RABOBANK["client_secret"]

        self.iban_check_url = settings.RABOBANK["iban_check_url"]
        self.scope = 'surepay:ibannamecheck:read'

        self.access_token = None
        self.token_expiry = None

    def _load_private_key(self):
        """Load the private key with password if provided"""
        try:
            # Load the private key with password
            with open(self.private_key, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=self.cert_pass.encode() if self.cert_pass else None,
                    backend=default_backend(),
                )
            # Serialize the private key back to PEM format
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            return private_key_pem
        except Exception as e:
            raise Exception(f"Failed to load private key: {e}")

    def _refresh_token(self):
        # Load the private key with password
        private_key_pem = self._load_private_key()

        # Create temporary files for the certificates
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as temp_cert:
            # Copy the public certificate content
            with open(self.public_cert, "r") as cert_file:
                temp_cert.write(cert_file.read())
            temp_cert_path = temp_cert.name

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".pem", delete=False
        ) as temp_key:
            # Write the decrypted private key
            temp_key.write(private_key_pem)
            temp_key_path = temp_key.name

        try:
            # Create Basic auth header
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            auth_header = f"Basic {encoded_credentials}"

            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                },
                cert=(temp_cert_path, temp_key_path),
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Response body: {response.text}")

            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            self.token_expiry = int(time.time()) + int(data.get("expires_in", 1800))
        finally:
            # Clean up temporary files
            os.unlink(temp_cert_path)
            os.unlink(temp_key_path)

    def _get_token(self):
        if not self.access_token or (self.token_expiry and time.time() > self.token_expiry - 60):
            self._refresh_token()
        return self.access_token

    def check_iban_name(self, iban, name):
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json"
        }
        payload = {
            "accountId": {
                "value": iban,
                "type": "IBAN"
            },
            "name": name
        }
        response = requests.post(self.iban_check_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
