from urllib.parse import urlparse

import http_sfv
from requests_http_signature import HTTPSignatureAuth, algorithms, HTTPSignatureKeyResolver
from http_message_signatures import exceptions, structures, resolvers
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key

from django.urls import resolve, Resolver404
from rest_framework import authentication

from bluebottle.activity_pub.utils import is_local
from bluebottle.activity_pub.models import Actor


class DjangoRequestComponentResolver(resolvers.HTTPSignatureComponentResolver):
    def __init__(self, message):
        self.message = message
        self.message_type = "request"

        if hasattr(message, 'build_absolute_uri'):
            self.url = str(message.build_absolute_uri())
        else:
            self.url = message.url

        self.headers = structures.CaseInsensitiveDict(message.headers)


class DjangoHTTPSignatureAuth(HTTPSignatureAuth):
    component_resolver_class = DjangoRequestComponentResolver

    @classmethod
    def get_body(cls, message):
        if message.method == 'GET':
            return None
        else:
            return super().get_body(message)


class JSONLDKeyResolver(HTTPSignatureKeyResolver):
    def get_actor(self, key_id):
        try:
            if is_local(key_id):
                resolved_url = resolve(urlparse(key_id).path)
                return Actor.objects.filter(pk=resolved_url.kwargs['pk']).first()
            return Actor.objects.filter(iri=key_id).first()
        except (Resolver404, KeyError, TypeError, ValueError, Actor.DoesNotExist):
            return None

    def resolve_public_key(self, key_id):
        actor = self.get_actor(key_id)
        public_key = getattr(actor, 'public_key', None)
        public_key_pem = getattr(public_key, 'public_key_pem', None)
        if public_key_pem:
            return load_pem_public_key(bytes(public_key_pem, encoding='utf-8'))

    def resolve_private_key(self, key_id):
        actor = self.get_actor(key_id)
        public_key = getattr(actor, 'public_key', None)
        private_key = getattr(public_key, 'private_key', None)
        private_key_pem = getattr(private_key, 'private_key_pem', None)
        if private_key_pem:
            return load_pem_private_key(bytes(private_key_pem, encoding='utf-8'), password=None)


key_resolver = JSONLDKeyResolver()


class HTTPSignatureAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        if 'Signature' in request.headers:
            signature_input = http_sfv.Dictionary()
            signature_input.parse(request.headers['Signature-Input'].encode())
            algorithm = 'ed25519'
            for input in signature_input.values():
                if 'alg' in input.params:
                    algorithm = input.params['alg']

            try:
                verify_result = DjangoHTTPSignatureAuth.verify(
                    request,
                    signature_algorithm=getattr(algorithms, algorithm.upper()),
                    key_resolver=key_resolver
                )
                actor = key_resolver.get_actor(verify_result.parameters['keyid'])
                if actor:
                    return (None, actor)
            except (Actor.DoesNotExist, TypeError, ValueError):
                pass
            except exceptions.InvalidSignature as e:
                print(e)
