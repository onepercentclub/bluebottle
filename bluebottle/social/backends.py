from social.backends.facebook import FacebookOAuth2


class NoStateFacebookOAuth2(FacebookOAuth2):
    name = 'facebook'
    STATE_PARAMETER = False
    REDIRECT_STATE = False

    def extra_data(self, *args, **kwargs):
        result = super(NoStateFacebookOAuth2, self).extra_data(*args, **kwargs)
        if 'scope' in kwargs['request']:
            result['requested_scope'] = kwargs['request'].get('scope').split(',')
        return result
