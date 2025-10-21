from social_core.backends.facebook import FacebookAppOAuth2
from social_core.backends.google import GoogleOAuth2


class NoStateFacebookOAuth2(FacebookAppOAuth2):
    name = 'facebook'
    STATE_PARAMETER = None
    REDIRECT_STATE = None


class NoStateGoogleOAuth2(GoogleOAuth2):
    name = 'google'
    STATE_PARAMETER = None
    REDIRECT_STATE = None

    def get_redirect_uri(self, *arg, **kwargs):
        return 'postmessage'
