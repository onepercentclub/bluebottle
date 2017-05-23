import json
from social.backends.facebook import FacebookAppOAuth2


class NoStateFacebookOAuth2(FacebookAppOAuth2):
    name = 'facebook'
    STATE_PARAMETER = False
    REDIRECT_STATE = False

    def process_refresh_token_response(self, response, *args, **kwargs):
        return json.loads(response.content)
