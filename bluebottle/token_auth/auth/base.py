import logging

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from bluebottle.token_auth.exceptions import TokenAuthenticationError

from bluebottle.utils.models import get_default_language
from django.utils import translation


logger = logging.getLogger(__name__)


class BaseTokenAuthentication():
    """
    Base class for TokenAuthentication.
    """
    settings = {}

    def __init__(self, request):
        self.request = request

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
        Set all user data that we got from the SSO service and store it
        on the user.
        """
        user_model = get_user_model()()
        return dict([(key, value) for key, value in list(data.items()) if hasattr(user_model, key)])

    def get_location(self):
        pass

    def set_location(self, user, data):
        location = self.get_location()

        if location and not user.location_verified:
            user.location = location
            user.save()

    def get_segments(self):
        return {}

    def set_segments(self, user, data):
        segments = self.get_segments()
        for segment_type_id, segment in segments.items():
            if (
                [segment] != user.segments.filter(segment_type__id=segment_type_id) and
                not user.segments.filter(
                    segment_type__id=segment_type_id, usersegment__verified=True
                ).count()
            ):
                user.segments.remove(*user.segments.filter(segment_type__id=segment_type_id))
                try:
                    user.segments.add(segment)
                except IntegrityError as e:
                    logger.error(e)

    def get_groups(self):
        return []

    def set_groups(self, user, data):
        groups = self.get_groups()

        for group, is_staff, is_admin in groups:
            if is_staff:
                user.is_staff = True

            if is_admin:
                user.is_superuser = True

            user.groups.add(group)

        user.save()

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
                    user = user_model.objects.get(email__iexact=user_data['email'])
                except (KeyError, user_model.DoesNotExist):
                    if self.settings.get('provision', True):
                        user = user_model(**user_data)
                        # Users provisioned through SSO should not be able to log in with a password
                        user.set_unusable_password()
                        user.save()
                        created = True
                    else:
                        logger.error('Login error: User not found, and provisioning is disabled')
                        raise TokenAuthenticationError(
                            "Account not found"
                        )

        if not created:
            user_model.objects.filter(pk=user.pk).update(**user_data)
            user.refresh_from_db()

        with translation.override(get_default_language()):
            self.set_location(user, data)
            self.set_segments(user, data)
            self.set_groups(user, data)

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
