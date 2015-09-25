from social.backends.facebook import FacebookOAuth2


class NoStateFacebookOAuth2(FacebookOAuth2):
    name = 'facebook'
    STATE_PARAMETER = False
    REDIRECT_STATE = False
