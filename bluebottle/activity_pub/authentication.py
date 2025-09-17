import http_sfv

from rest_framework import authentication
from requests_http_signature import HTTPSignatureAuth, algorithms
from http_message_signatures import exceptions, structures, resolvers

from bluebottle.activity_pub.adapters import JSONLDKeyResolver
from bluebottle.activity_pub.models import Actor


class DjangoRequestComponentResolver(resolvers.HTTPSignatureComponentResolver):
    def __init__(self, message):
        self.message = message
        self.message_type = "request"
        self.url = str(message.build_absolute_uri())
        self.headers = structures.CaseInsensitiveDict(message.headers)


class DjangoHTTPSignatureAuth(HTTPSignatureAuth):
    component_resolver_class = DjangoRequestComponentResolver


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
                    key_resolver=JSONLDKeyResolver()
                )
                return (None, Actor.objects.get(url=verify_result.parameters['keyid']))
            except (exceptions.InvalidSignature, Actor.DoesNotExist) as e:
                print(e)
