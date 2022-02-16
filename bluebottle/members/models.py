from __future__ import absolute_import

from builtins import object

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _
from future.utils import python_2_unicode_compatible
from multiselectfield import MultiSelectField

from bluebottle.bb_accounts.models import BlueBottleBaseUser
from bluebottle.geo.models import Place
from bluebottle.utils.models import BasePlatformSettings
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


class MemberPlatformSettings(BasePlatformSettings):
    LOGIN_METHODS = (
        ('password', _('Email/password combination')),
        ('SSO', _('Company SSO')),
    )

    closed = models.BooleanField(
        default=False, help_text=_('Require login before accessing the platform')
    )
    login_methods = MultiSelectField(max_length=100, choices=LOGIN_METHODS, default=['password'])
    confirm_signup = models.BooleanField(
        default=False, help_text=_('Require verifying the user\'s email before signup')
    )
    email_domain = models.CharField(
        blank=True, null=True,
        help_text=_('Domain that all email should belong to'),
        max_length=256
    )
    session_only = models.BooleanField(
        default=False,
        help_text=_('Limit user session to browser session')
    )

    require_consent = models.BooleanField(
        default=False, help_text=_('Require users to consent to cookies')
    )
    consent_link = models.CharField(
        default='"https://goodup.com/cookie-policy"',
        help_text=_('Link more information about the platforms cookie policy'),
        max_length=255
    )

    background = models.ImageField(
        null=True, blank=True, upload_to='site_content/',
        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    enable_gender = models.BooleanField(
        default=False,
        help_text=_('Show gender question in profile form')
    )

    enable_birthdate = models.BooleanField(
        default=False,
        help_text=_('Show birthdate question in profile form')
    )

    enable_address = models.BooleanField(
        default=False,
        help_text=_('Show address question in profile form')
    )

    enable_segments = models.BooleanField(
        default=False,
        help_text=_('Enable segments for users e.g. department or job title.')
    )

    create_segments = models.BooleanField(
        default=False,
        help_text=_('Create new segments when a user logs in. '
                    'Leave unchecked if only priorly specified ones should be used.')
    )

    anonymization_age = models.IntegerField(
        default=0,
        help_text=_("The number of days after which user data should be anonymised. 0 for no anonymisation")
    )

    class Meta(object):
        verbose_name_plural = _('member platform settings')
        verbose_name = _('member platform settings')


@python_2_unicode_compatible
class Member(BlueBottleBaseUser):
    verified = models.BooleanField(default=False, blank=True, help_text=_('Was verified for voting by recaptcha.'))
    subscribed = models.BooleanField(
        _('Matching'),
        default=False,
        help_text=_("Monthly overview of activities that match this person's profile")
    )

    remote_id = models.CharField(_('remote_id'),
                                 max_length=75,
                                 blank=True,
                                 null=True)
    last_logout = models.DateTimeField(_('Last Logout'), blank=True, null=True)

    scim_external_id = models.CharField(
        _('external SCIM id'),
        max_length=75,
        blank=True,
        null=True
    )

    place = models.ForeignKey(Place, null=True, blank=True, on_delete=models.SET_NULL)

    matching_options_set = models.DateTimeField(
        null=True, blank=True, help_text=_('When the user updated their matching preferences.')
    )

    segments = models.ManyToManyField(
        'segments.segment',
        verbose_name=_('Segment'),
        related_name='users',
        blank=True,
        through='members.UserSegment'
    )

    def __init__(self, *args, **kwargs):
        super(Member, self).__init__(*args, **kwargs)

        try:
            self._previous_last_seen = self.last_seen
        except ObjectDoesNotExist:
            self._previous_last_seen = None

    class Analytics(object):
        type = 'member'
        tags = {}
        fields = {
            'user_id': 'id'
        }

        @staticmethod
        def extra_tags(obj, created):
            if created:
                return {'event': 'signup'}
            else:
                # The skip method below is being used to ensure analytics are only
                # triggered if the last_seen field has changed.
                return {'event': 'seen'}

        @staticmethod
        def skip(obj, created):
            # Currently only the signup (created) event is being recorded
            # and when the last_seen changes.
            return False if created or obj.last_seen != obj._previous_last_seen else True

        @staticmethod
        def timestamp(obj, created):
            # This only serves the purpose when we record the member created logs
            # We need to modify this if we ever record member deleted
            if created:
                return obj.date_joined
            else:
                return obj.updated

    @property
    def initials(self):
        initials = ''
        if self.first_name:
            initials += self.first_name[0]
        if self.last_name:
            initials += self.last_name[0]

        return initials

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not (self.is_staff or self.is_superuser) and self.submitted_initiative_notifications:
            self.submitted_initiative_notifications = False
        super(Member, self).save(*args, **kwargs)


class UserSegment(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    segment = models.ForeignKey('segments.segment', on_delete=models.CASCADE)
    verified = models.BooleanField(default=True)


class UserActivity(models.Model):

    user = models.ForeignKey(Member, null=True, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=200, null=True, blank=True)

    class Meta(object):
        verbose_name = _('User activity')
        verbose_name_plural = _('User activities')
        ordering = ['-created']


from . import signals  # noqa
