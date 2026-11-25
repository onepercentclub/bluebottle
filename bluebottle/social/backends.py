from social_core.backends.facebook import FacebookAppOAuth2
from social_core.backends.google import GoogleOAuth2
from social_core.exceptions import AuthException


class NoStateFacebookOAuth2(FacebookAppOAuth2):
    name = 'facebook'
    STATE_PARAMETER = None
    REDIRECT_STATE = None

    def load_signed_request(self, signed_request):
        response = super().load_signed_request(signed_request)
        if response is None:
            raise AuthException(self, 'Invalid signed request')
        return response


class NoStateGoogleOAuth2(GoogleOAuth2):
    name = 'google'
    STATE_PARAMETER = None
    REDIRECT_STATE = None

    def get_redirect_uri(self, *arg, **kwargs):
        return 'postmessage'
