from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import signing

from bluebottle.clients import properties


class LoginTokenGenerator(PasswordResetTokenGenerator):
    def make_token(self, user):
        data = {
            'user_id': user.pk,
            'last_login': user.last_login.strftime('%s') if user.last_login else None
        }
        return signing.dumps(data)

    def check_token(self, user, token):
        """
        Check that a login token is correct for a given user.

        Adds a check for properties.LOGIN_TOKEN_TIMEOUT_SECONDS
        """
        try:
            data = signing.loads(token, max_age=properties.TOKEN_LOGIN_TIMEOUT)
        except signing.BadSignature:
            return False

        return (
            (
                (data['last_login'] is None and user.last_login is None) or
                data['last_login'] == user.last_login.strftime('%s')
            ) and
            data['user_id'] == user.pk
        )


login_token_generator = LoginTokenGenerator()
