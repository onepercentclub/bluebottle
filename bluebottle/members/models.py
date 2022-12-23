from __future__ import absolute_import

from builtins import object
from datetime import timedelta, datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Sum
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from future.utils import python_2_unicode_compatible
from multiselectfield import MultiSelectField

from bluebottle.bb_accounts.models import BlueBottleBaseUser
from bluebottle.geo.models import Place
from bluebottle.utils.models import BasePlatformSettings
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection
from ..segments.models import SegmentType
from ..time_based.models import TimeContribution


class MemberPlatformSettings(BasePlatformSettings):
    LOGIN_METHODS = (
        ('password', _('Email/password combination')),
        ('SSO', _('Company SSO')),
    )

    DISPLAY_MEMBER_OPTIONS = (
        ('full_name', _('Full name')),
        ('first_name', _('First name')),
    )

    REQUIRED_QUESTIONS_OPTIONS = (
        ('login', _('After log in')),
        ('contribution', _('When making a contribution')),
    )

    closed = models.BooleanField(
        default=False, help_text=_('Require login before accessing the platform')
    )
    create_initiatives = models.BooleanField(
        default=True, help_text=_('Members can create initiatives')
    )
    do_good_hours = models.PositiveIntegerField(
        _('Impact hours'),
        null=True, blank=True,
        help_text=_("Leave empty if this feature won't be used.")
    )
    fiscal_month_offset = models.IntegerField(
        _('Fiscal year offset'),
        help_text=_('Set the number of months your fiscal year will be offset by. '
                    'This will also take into account how the impact metrics are shown on the homepage. '
                    'e.g. If the year starts from September (so earlier) then this value should be -4.'),
        default=0)

    reminder_q1 = models.BooleanField(
        _('Reminder Q1'),
        default=False,
    )
    reminder_q2 = models.BooleanField(
        _('Reminder Q2'),
        default=False,
    )
    reminder_q3 = models.BooleanField(
        _('Reminder Q3'),
        default=False,
    )
    reminder_q4 = models.BooleanField(
        _('Reminder Q4'),
        default=False,
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

    required_questions_location = models.CharField(
        choices=REQUIRED_QUESTIONS_OPTIONS,
        max_length=12,
        default='login',
        help_text=_(
            'When should the user be asked to complete their required profile fields?'
        )
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
        help_text=_("Require members to enter or verify the fields below once after logging in.")
    )

    require_office = models.BooleanField(
        _('Office location'),
        default=False,
        help_text=_('Require members to enter their office location.')
    )
    require_address = models.BooleanField(
        _('Address'),
        default=False,
        help_text=_('Require members to enter their address.')
    )
    require_phone_number = models.BooleanField(
        _('Phone number'),
        default=False,
        help_text=_('Require members to enter their phone number.')
    )
    require_birthdate = models.BooleanField(
        _('Birthdate'),
        default=False,
        help_text=_('Require members to enter their date of birth.')
    )

    verify_office = models.BooleanField(
        _('Verify SSO data office location'),
        default=False,
        help_text=_('Require members to verify their office location once if it is filled via SSO.')
    )

    display_member_names = models.CharField(
        _('Display member names'),
        choices=DISPLAY_MEMBER_OPTIONS,
        max_length=12,
        default='full_name',
        help_text=_(
            'How names of members will be displayed for visitors and other members.'
            'If first name is selected, then the names of initiators and activity manager '
            'will remain displayed in full and Activity managers and initiators will see '
            'the full names of their participants. And staff members will see all names in full.'
        )
    )

    retention_anonymize = models.PositiveIntegerField(
        _('Anonymise'),
        default=None,
        null=True,
        blank=True,
        help_text=_('Set the number of months after which user data will be anonymised.')

    )

    retention_delete = models.PositiveIntegerField(
        _('Delete'),
        default=None,
        null=True,
        blank=True,
        help_text=_('Set the number of months after which user data will be deleted.')

    )

    @property
    def fiscal_year_start(self):
        offset = self.fiscal_month_offset
        month_start = (datetime(2000, 1, 1) + relativedelta(months=offset)).month
        return (now() + relativedelta(months=offset)).replace(month=month_start, day=1, hour=0, second=0)

    @property
    def fiscal_year_end(self):
        return self.fiscal_year_start + relativedelta(years=1) - timedelta(seconds=1)

    def fiscal_year(self):
        offset = self.fiscal_month_offset
        return (now() - relativedelta(months=offset)).year

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
    receive_reminder_emails = models.BooleanField(
        _('Receive reminder emails'),
        default=True,
        help_text=_("User receives emails reminding them about their do good hours")
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

    @property
    def required(self):
        required = []
        for segment_type in SegmentType.objects.filter(required=True).all():
            if not self.segments.filter(
                usersegment__verified=True, segment_type=segment_type
            ).count():
                required.append(f'segment_type.{segment_type.id}')

        platform_settings = MemberPlatformSettings.load()

        if platform_settings.require_office and (
            not self.location or
            (platform_settings.verify_office and not self.location_verified)
        ):
            required.append('location')

        for attr in ['birthdate', 'phone_number']:
            if getattr(platform_settings, f'require_{attr}') and not getattr(self, attr):
                required.append(attr)

        if platform_settings.require_address and not (self.place and self.place.complete):
            required.append('address')

        return required

    def __str__(self):
        return self.full_name

    def get_hours(self, status):
        platform_settings = MemberPlatformSettings.load()
        year_start = platform_settings.fiscal_year_start
        year_end = platform_settings.fiscal_year_end
        hours = TimeContribution.objects.filter(
            contributor__user=self,
            status=status,
            start__gte=year_start,
            start__lte=year_end
        ).aggregate(hours=Sum('value'))['hours']
        if hours:
            return hours.seconds / 3600 + hours.days * 24
        return 0.0

    @property
    def hours_spent(self):
        return self.get_hours('succeeded')

    @property
    def hours_planned(self):
        return self.get_hours('new')

    def save(self, *args, **kwargs):
        if not (self.is_staff or self.is_superuser) and self.submitted_initiative_notifications:
            self.submitted_initiative_notifications = False
        super(Member, self).save(*args, **kwargs)


class UserSegment(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    segment = models.ForeignKey('segments.segment', on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)


class UserActivity(models.Model):

    user = models.ForeignKey(Member, null=True, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=200, null=True, blank=True)

    class Meta(object):
        verbose_name = _('User activity')
        verbose_name_plural = _('User activities')
        ordering = ['-created']


from . import signals  # noqa
