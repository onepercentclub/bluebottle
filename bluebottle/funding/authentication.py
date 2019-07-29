from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication, get_authorization_header


class DonationAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if len(auth) == 2 and auth[0].lower() == 'donation':
            return (AnonymousUser(), auth[1])
