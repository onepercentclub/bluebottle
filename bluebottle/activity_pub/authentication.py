from requests import Request

from rest_framework import authentication
from requests_http_signature import HTTPSignatureAuth, algorithms
from http_message_signatures import exceptions

from bluebottle.activity_pub.adapters import JSONLDKeyResolver
from bluebottle.activity_pub.models import Actor


class HTTPSignatureAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        if 'Signature' in request.headers:
            prepared_request = Request(
                request.method.upper(), 
                request.build_absolute_uri(), 
                data=request.body, 
                headers=request.headers
            ).prepare()

            try: 
                verify_result = HTTPSignatureAuth.verify(
                    prepared_request,
                    signature_algorithm=algorithms.ED25519,
                    key_resolver=JSONLDKeyResolver()
                )
                return (None, Actor.objects.get(url=verify_result.parameters['keyid']))
            except (exceptions.InvalidSignature, Actor.DoesNotExist) as e:
                print(e)