from requests import Request

from django.test import RequestFactory
from django.db import connection

from bluebottle.activity_pub.authentication import (
    DjangoHTTPSignatureAuth, key_resolver
)

from requests_http_signature import algorithms


class SignedRequestFactory(RequestFactory):
    def __init__(self, key_id, *args, **kwargs):
        self.signer = DjangoHTTPSignatureAuth(
            key_resolver=key_resolver, key_id=key_id, signature_algorithm=algorithms.ED25519
        )
        self.overrides = {}

        super().__init__(*args, **kwargs)

    def override(self, **kwargs):
        self.overrides = dict(**self.overrides, **kwargs)

    def request(self, **kwargs):
        kwargs['SERVER_NAME'] = connection.tenant.domain_url
        result = super().request(**kwargs)

        path = self.overrides.get('path', result.path)
        data = self.overrides.get('data', result.body)

        request = Request(
            result.method,
            f'http://test.localhost{path}',
            data=data,
            headers=result.headers
        ).prepare()

        signed = self.signer(request)

        for header, value in signed.headers.items():
            meta_key = f'HTTP_{header.replace("-", "_").upper()}'
            if meta_key not in result.META:
                result.META[meta_key] = value

        result.__dict__.pop('headers')

        return result
