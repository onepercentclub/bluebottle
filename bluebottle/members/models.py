from __future__ import absolute_import

from future.utils import python_2_unicode_compatible

from builtins import object
from adminsortable.models import SortableMixin
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectField

from bluebottle.bb_accounts.models import BlueBottleBaseUser
from bluebottle.geo.models import Place
from bluebottle.utils.models import BasePlatformSettings


class CustomMemberFieldSettings(SortableMixin):

    member_settings = models.ForeignKey('members.MemberPlatformSettings',
                                        null=True,
                                        related_name='extra_fields')

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, null=True, blank=True)
    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    @property
    def slug(self):
        return slugify(self.name)

    class Meta(object):
        ordering = ['sequence']


class CustomMemberField(models.Model):
    member = models.ForeignKey('members.Member', related_name='extra')
    field = models.ForeignKey('members.CustomMemberFieldSettings')
    value = models.CharField(max_length=5000, null=True, blank=True)


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

    require_consent = models.BooleanField(
        default=False, help_text=_('Require users to consent to cookies')
    )
    consent_link = models.CharField(
        default='/pages/terms-and-conditions',
        help_text=_('Link more information about the platforms policy'),
        max_length=255
    )

    background = models.ImageField(null=True, blank=True, upload_to='site_content/')

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
        default=False, help_text=_('Member is interrested in receiving updates on matching projects')
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

    places = GenericRelation(Place)

    matching_options_set = models.DateTimeField(
        null=True, blank=True, help_text=_('When the user updated their matching preferences.')
    )

    segments = models.ManyToManyField(
        'segments.segment',
        verbose_name=_('Segment'),
        related_name='users',
        blank=True,
        null=True
    )

    def __init__(self, *args, **kwargs):
        super(Member, self).__init__(*args, **kwargs)

        try:
            self._previous_last_seen = self.last_seen
        except ObjectDoesNotExist:
            self._previous_last_seen = None

    @property
    def place(self):
        try:
            return self.places.get()
        except Place.DoesNotExist:
            return None

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
        return u"{} | {}".format(self.full_name, self.email)


class UserActivity(models.Model):

    user = models.ForeignKey(Member, null=True)
    created = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=200, null=True, blank=True)

    class Meta(object):
        verbose_name = _('User activity')
        verbose_name_plural = _('User activities')
        ordering = ['-created']


from . import signals  # noqa
