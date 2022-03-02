from builtins import object
import logging

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from bluebottle.geo.models import Location
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.models import Segment, SegmentType
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
        Set all user data that we got from the SSO service and store it
        on the user.
        """
        user_model = get_user_model()()
        return dict([(key, value) for key, value in list(data.items()) if hasattr(user_model, key)])

    def set_location(self, user, data):
        if 'location.slug' in data:
            try:
                user.location = Location.objects.get(slug=data['location.slug'])
                user.save()
            except Location.DoesNotExist:
                pass

    def get_segments_from_data(self, data):
        segment_list = {}
        segment_data = [
            (field, value)
            for field, value in list(data.items())
            if field.startswith('segment.')
        ]
        for (path, value) in segment_data:
            type_slug = path.split('.')[-1]
            try:
                segment_type = SegmentType.objects.get(slug=type_slug)
            except SegmentType.DoesNotExist:
                logger.info('SSO Error: Missing segment type: {}'.format(type_slug))
                return

            if not isinstance(value, (list, tuple)):
                value = [value]
            segment_list[segment_type.id] = []
            for val in value:
                try:
                    segment = Segment.objects.filter(
                        segment_type__slug=type_slug,
                    ).extra(
                        where=['%s ILIKE ANY (alternate_names)'],
                        params=[val, ]
                    ).get()
                    segment_list[segment_type.id].append(segment)
                except Segment.DoesNotExist:
                    if MemberPlatformSettings.load().create_segments:
                        segment = Segment.objects.create(
                            segment_type=segment_type,
                            name=val,
                            alternate_names=[val]
                        )
                        segment_list[segment_type.id].append(segment)
                except IntegrityError:
                    pass
        return segment_list

    def set_segments(self, user, data):
        segment_list = self.get_segments_from_data(data)
        for segment_type_id, segments in segment_list.items():
            if segments != user.segments.filter(segment_type__id=segment_type_id):
                user.segments.remove(*user.segments.filter(segment_type__id=segment_type_id))
                user.segments.add(*segments)

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

        self.set_location(user, data)
        self.set_segments(user, data)

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
