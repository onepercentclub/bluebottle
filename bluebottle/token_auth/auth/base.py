import logging

from django.contrib.auth import get_user_model

from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.utils import get_settings

logger = logging.getLogger(__name__)


class BaseTokenAuthentication(object):
    """
    Base class for TokenAuthentication.
    """
    def __init__(self, request, **kwargs):
        self.args = kwargs
        self.request = request

        self.settings = get_settings()

    def sso_url(self, target_url=None):
        raise NotImplementedError()

    @property
    def target_url(self):
        return None

    def authenticate_request(self):
        """
        Authenticate the request. Should return a dict containing data
        representing the authenticated user.

        Typically it should at least have an <email>.
        {'email': <email>}
        """
        raise NotImplementedError()

    def get_user_data(self, data):
        """
        Set al user data that we got from the SSO service and store it
        on the user.
        """
        user_model = get_user_model()()
        return dict([(key, value) for key, value in data.items() if hasattr(user_model, key)])

    def get_or_create_user(self, data):
        """
        Get or create the user.
        """
        user_data = self.get_user_data(data)
        user_model = get_user_model()
        created = False
        try:
            user = user_model.objects.get(remote_id=data['remote_id'])
        except user_model.DoesNotExist:
            try:
                user = user_model.objects.get(remote_id__iexact=data['remote_id'])
                user.remote_id = data['remote_id']
                user.save()
            except user_model.DoesNotExist:
                try:
                    user = user_model.objects.get(email=user_data['email'])
                except (KeyError, user_model.DoesNotExist):
                    if self.settings.get('provision', True):
                        user = user_model.objects.create(**user_data)
                        created = True
                    else:
                        logger.error('Login error: User not found, and provisioning is disabled')
                        raise TokenAuthenticationError(
                            "Account not found"
                        )

        if not created:
            user_model.objects.filter(pk=user.pk).update(**user_data)
            user.refresh_from_db()

        return user, created

    def finalize(self, user, data):
        """
        Finalize the request. Used for example to store used tokens,
        to prevent replay attacks
        """
        pass

    def process_logout(self):
        """
        Log out
        """
        pass

    def get_metadata(self):
        raise NotImplementedError()

    def authenticate(self):
        data = self.authenticate_request()
        data['is_active'] = True

        user, created = self.get_or_create_user(data)
        self.finalize(user, data)

        return user, created
