from django.apps import apps
from django.contrib.auth.tokens import PasswordResetTokenGenerator as BasePasswordResetTokenGenerator


class PasswordResetTokenGenerator(BasePasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Same as Django's implementation, except for the source of the last login
        # Looked up lazily: importing members.models here would be circular
        last_login = apps.get_model('members', 'AuthenticationLog').last_login(user)
        login_timestamp = (
            ''
            if last_login is None
            else last_login.replace(microsecond=0, tzinfo=None)
        )
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, '') or ''
        return f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'


password_reset_token_generator = PasswordResetTokenGenerator()
