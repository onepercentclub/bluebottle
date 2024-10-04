from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication, get_authorization_header


class DonorAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if len(auth) == 2 and auth[0].lower().decode() == 'donation':
            return AnonymousUser(), auth[1].decode()


class ClientSecretAuthentication(BaseAuthentication):

    def authenticate(self, request):
        client_secret = request.data.get('client_secret', None)
        if client_secret:
            return AnonymousUser(), client_secret
