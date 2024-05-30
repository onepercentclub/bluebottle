import uuid
from html import unescape
from urllib.parse import urlencode

import pytz
from django.db import connection
from django.db.models import Sum
from django.utils import timezone
from django.utils.timezone import now
from djchoices.choices import DjangoChoices, ChoiceItem
from parler.models import TranslatableModel, TranslatedFields
from polymorphic.models import PolymorphicModel
from timezonefinder import TimezoneFinder

from bluebottle.activities.models import Activity, Contributor, Contribution, Team
from bluebottle.files.fields import PrivateDocumentField
from bluebottle.fsm.triggers import TriggerMixin
from bluebottle.geo.models import Geolocation
from bluebottle.time_based.validators import (
    PeriodActivityRegistrationDeadlineValidator, CompletedSlotsValidator,
    HasSlotValidator
)
from bluebottle.utils.models import ValidatedModelMixin, AnonymizationMixin
from bluebottle.utils.utils import get_current_host, get_current_language, to_text
from bluebottle.utils.widgets import get_human_readable_duration

tf = TimezoneFinder()

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeBasedActivity(Activity):
    ONLINE_CHOICES = (
        (None, 'Not set yet'),
        (True, 'Yes, anywhere/online'),
        (False, 'No, enter a location')
    )
    capacity = models.PositiveIntegerField(
        _('attendee limit'),
        help_text=_('Number of participants or teams that can join'),
        null=True, blank=True)

    registration_deadline = models.DateField(
        _('registration deadline'),
        null=True,
        blank=True
    )

    expertise = models.ForeignKey(
        'time_based.Skill',
        verbose_name=_('skill'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    review_document_enabled = models.BooleanField(
        _('Upload documents'),
        help_text=_('Allow participants to upload documents that support their application.'),
        null=True, default=False
    )

    REGISTRATION_FLOW_CHOICES = (
        ('none', _('No')),
        ('question', _('Ask a single question on the platform.')),
        ('link', _('Direct the participants to a questionnaire on an external website like Microsoft forms.')),
    )

    registration_flow = models.CharField(
        _('Ask a question'),
        help_text=_('Do you want to ask any questions to your participants when they join your activity?'),
        choices=REGISTRATION_FLOW_CHOICES,
        default='none',
        max_length=100
    )

    review = models.BooleanField(
        _('Review participants'),
        help_text=_('Activity manager accepts or rejects participants or teams.'),
        null=True, default=None)

    review_title = models.CharField(
        _('Question label'),
        help_text=_('This is the question that participants will answer.'),
        max_length=255,
        null=True, blank=True
    )

    review_description = models.TextField(
        _('Question description'),
        help_text=_('Give some more context to help the participant answer the question.'),
        null=True, blank=True
    )
    review_link = models.URLField(
        _('External website link'),
        help_text=_('Direct participants to a questionnaire created from an external website like Microsoft forms.'),
        max_length=255,
        null=True, blank=True
    )

    preparation = models.DurationField(
        _('Preparation time'),
        null=True, blank=True,
    )

    activity_type = _('Time-based activity')

    @property
    def local_timezone(self):
        if self.location and self.location.position:
            tz_name = tf.timezone_at(
                lng=self.location.position.x,
                lat=self.location.position.y
            )
            return pytz.timezone(tz_name)

    @property
    def utc_offset(self):
        tz = self.local_timezone or timezone.get_current_timezone()
        if self.start and tz:
            return self.start.astimezone(tz).utcoffset().total_seconds() / 60

    @property
    def required_fields(self):
        return super().required_fields + [
            "title",
            "description",
            "review",
        ]

    @property
    def participants(self):
        return self.contributors.instance_of(
            PeriodParticipant,
            DateParticipant,
            DeadlineParticipant,
            PeriodicParticipant,
            ScheduleParticipant,
            TeamScheduleParticipant
        )

    @property
    def pending_participants(self):
        return self.participants.filter(status="new")

    @property
    def cancelled_participants(self):
        return self.participants.filter(status="cancelled")

    @property
    def active_participants(self):
        return self.participants.filter(
            status__in=["accepted", "new"]
        )

    @property
    def accepted_participants(self):
        return self.participants.filter(
            status__in=["accepted", "succeeded"]
        )

    @property
    def succeeded_contributor_count(self):
        return self.accepted_participants.count() + self.deleted_successful_contributors

    @property
    def durations(self):
        return TimeContribution.objects.filter(
            contributor__activity=self
        )

    @property
    def active_durations(self):
        return self.durations.filter(
            contributor__status__in=('new', 'accepted')
        )

    @property
    def values(self):
        return TimeContribution.objects.filter(
            contributor__activity=self,
            status='succeeded'
        )

    @property
    def details(self):
        details = unescape(
            u'{}\n{}'.format(
                to_text.handle(self.description), self.get_absolute_url()
            )
        )
        return details


class SlotSelectionChoices(DjangoChoices):
    all = ChoiceItem('all', label=_("All"))
    free = ChoiceItem('free', label=_("Free"))


class DateActivity(TimeBasedActivity):
    old_online_meeting_url = models.TextField(
        _('online meeting link'),
        blank=True, default='',
        db_column='online_meeting_url'
    )
    duration_period = 'overall'

    validators = [
        CompletedSlotsValidator,
        HasSlotValidator
    ]

    @property
    def start(self):
        if self.slots.first():
            return self.slots.first().start.date()

    @property
    def active_slots(self):
        return self.slots.filter(status__in=['open', 'full', 'running', 'finished']).order_by('start', 'id')

    class Meta:
        verbose_name = _("Activity on a date")
        verbose_name_plural = _("Activities on a date")
        permissions = (
            ('api_read_dateactivity', 'Can view on a date activities through the API'),
            ('api_add_dateactivity', 'Can add on a date activities through the API'),
            ('api_change_dateactivity', 'Can change on a date activities through the API'),
            ('api_delete_dateactivity', 'Can delete on a date activities through the API'),

            ('api_read_own_dateactivity', 'Can view own on a date activities through the API'),
            ('api_add_own_dateactivity', 'Can add own on a date activities through the API'),
            ('api_change_own_dateactivity', 'Can change own on a date activities through the API'),
            ('api_delete_own_dateactivity', 'Can delete own on a date activities through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'activities/time-based/dates'

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        return u"{}/{}/activities/details/date/{}/{}".format(
            domain, language,
            self.pk,
            self.slug
        )

    @property
    def activity_date(self):
        first_slot = self.slots.order_by('start').first()
        if first_slot:
            return first_slot.start

    @property
    def uid(self):
        return '{}-{}-{}'.format(connection.tenant.client_name, 'dateactivity', self.pk)

    @property
    def end(self):
        return self.start + self.duration


class ActivitySlot(TriggerMixin, AnonymizationMixin, ValidatedModelMixin, models.Model):
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=40)
    title = models.CharField(
        _('title'),
        max_length=255,
        null=True, blank=True)

    capacity = models.PositiveIntegerField(_('attendee limit'), null=True, blank=True)

    is_online = models.BooleanField(
        _('is online'),
        choices=DateActivity.ONLINE_CHOICES,
        null=True, default=None
    )

    online_meeting_url = models.TextField(
        _('online meeting link'),
        blank=True, default=''
    )

    location = models.ForeignKey(
        Geolocation,
        verbose_name=_('location'),
        null=True, blank=True,
        on_delete=models.SET_NULL
    )

    location_hint = models.TextField(_('location hint'), null=True, blank=True)

    @property
    def uid(self):
        return '{}-{}-{}'.format(connection.tenant.client_name, 'dateactivityslot', self.pk)

    @property
    def owner(self):
        return self.activity.owner

    @property
    def initiative(self):
        return self.activity.initiative

    @property
    def local_timezone(self):
        if self.location and self.location.position:
            tz_name = tf.timezone_at(
                lng=self.location.position.x,
                lat=self.location.position.y
            )
            return pytz.timezone(tz_name)

    @property
    def utc_offset(self):
        tz = self.local_timezone or timezone.get_current_timezone()
        if self.start and tz:
            return self.start.astimezone(tz).utcoffset().total_seconds() / 60

    @property
    def google_calendar_link(self):
        def format_date(date):
            if date:
                return date.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

        details = self.activity.details
        if self.is_online and self.online_meeting_url:
            details += _('\nJoin: {url}').format(url=self.online_meeting_url)

        url = u'https://calendar.google.com/calendar/render'
        params = {
            'action': u'TEMPLATE',
            'text': self.activity.title,
            'dates': u'{}/{}'.format(
                format_date(self.start), format_date(self.start + self.duration)
            ),
            'details': details,
            'uid': self.uid,
        }

        if self.location:
            params['location'] = self.location.formatted_address
            if self.location_hint:
                params['location'] = f'{params["location"]} ({self.location_hint})'

        return u'{}?{}'.format(url, urlencode(params))

    @property
    def accepted_participants(self):
        return self.slot_participants.filter(
            status__in=['registered', 'new', 'succeeded'],
            participant__status='accepted'
        )

    @property
    def durations(self):
        return TimeContribution.objects.filter(
            slot_participant__slot=self
        )

    @property
    def active_durations(self):
        return self.durations.filter(
            slot_participant__participant__status__in=('new', 'accepted')
        )

    class Meta:
        abstract = True
        ordering = ['start', 'id']


class DateActivitySlot(ActivitySlot):
    activity = models.ForeignKey(DateActivity, related_name='slots', on_delete=models.CASCADE)

    start = models.DateTimeField(_('start date and time'), null=True, blank=True)
    duration = models.DurationField(_('duration'), null=True, blank=True)

    @property
    def required_fields(self):
        fields = super().required_fields + [
            'start',
            'duration',
            'is_online',
        ]

        if not self.is_online:
            fields.append('location')
        return fields

    @property
    def end(self):
        if self.start and self.duration:
            return self.start + self.duration

    @property
    def sequence(self):
        ids = list(self.activity.slots.values_list('id', flat=True))
        if len(ids) and self.id and self.id in ids:
            return ids.index(self.id) + 1
        return '-'

    @property
    def contributor_count(self):
        return self.slot_participants.filter(
            status__in=['registered', 'succeeded']
        ).filter(participant__status__in=['accepted']).count()

    @property
    def local_timezone(self):
        if self.location and self.location.position:
            tz_name = tf.timezone_at(
                lng=self.location.position.x,
                lat=self.location.position.y
            )
            return pytz.timezone(tz_name)

    @property
    def utc_offset(self):
        tz = self.local_timezone or timezone.get_current_timezone()
        if self.start and tz:
            return self.start.astimezone(tz).utcoffset().total_seconds() / 60

    def __str__(self):
        return "{} {}".format(_("Slot"), self.sequence)

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        return u"{}/{}/activities/details/date/{}/{}?slotId={}".format(
            domain, language,
            self.activity.pk,
            self.activity.slug,
            self.pk

        )

    @property
    def event_data(self):
        if self.end < now() or self.status not in ['open', 'full']:
            return None
        title = f'{self.activity.title} - {self.title or self.id}'
        location = ''
        if self.is_online:
            location = _('Anywhere/Online')
        elif self.location:
            location = self.location.locality or self.location.formatted_address or ''
            if self.location_hint:
                location += f" {self.location_hint}"

        return {
            'uid': f"{connection.tenant.client_name}-{self.id}",
            'summary': title,
            'description': self.activity.description,
            'organizer': self.activity.owner.email,
            'url': self.activity.get_absolute_url(),
            'location': location,
            'start_time': self.start,
            'end_time': self.end,
        }

    class Meta:
        verbose_name = _('slot')
        verbose_name_plural = _('slots')
        permissions = (
            ('api_read_dateactivityslot', 'Can view on date activity slots through the API'),
            ('api_add_dateactivityslot', 'Can add on a date activity slots through the API'),
            ('api_change_dateactivityslot', 'Can change on a date activity slots through the API'),
            ('api_delete_dateactivityslot', 'Can delete on a date activity slots through the API'),

            ('api_read_own_dateactivityslot', 'Can view own on a date activity slots through the API'),
            ('api_add_own_dateactivityslot', 'Can add own on a date activity slots through the API'),
            ('api_change_own_dateactivityslot', 'Can change own on a date activity slots through the API'),
            ('api_delete_own_dateactivityslot', 'Can delete own on a date activity slots through the API'),
        )
        ordering = ['start', 'id']

    class JSONAPIMeta:
        resource_name = 'activities/time-based/date-slots'


class DurationPeriodChoices(DjangoChoices):
    overall = ChoiceItem('overall', label=_("in total"))
    days = ChoiceItem('days', label=_("per day"))
    weeks = ChoiceItem('weeks', label=_("per week"))
    months = ChoiceItem('months', label=_("per month"))


class PeriodActivity(TimeBasedActivity):

    ONLINE_CHOICES = (
        (None, 'Not set yet'),
        (True, 'Yes, participants can join from anywhere or online'),
        (False, 'No, enter a location')
    )

    is_online = models.BooleanField(_('is online'), choices=ONLINE_CHOICES, null=True, default=None)

    location = models.ForeignKey(
        Geolocation, verbose_name=_('location'),
        null=True, blank=True, on_delete=models.SET_NULL
    )
    location_hint = models.TextField(_('location hint'), null=True, blank=True)

    start = models.DateField(
        _('Start date'),
        help_text=_('The first moment participants can start.'),
        null=True,
        blank=True
    )

    deadline = models.DateField(
        _('End date'),
        help_text=_('Participants can contribute until this date.'),
        null=True,
        blank=True
    )

    duration = models.DurationField(
        _('Activity duration'),
        help_text=_('How much time will a participant contribute?'),
        null=True,
        blank=True
    )

    duration_period = models.CharField(
        _('Recurring period'),
        max_length=20,
        blank=True,
        null=True,
        choices=DurationPeriodChoices.choices,
    )

    max_iterations = models.PositiveIntegerField(
        _('Max iterations'),
        help_text=_('How many weeks/months will a participant contribute to this activity?'),
        null=True,
        blank=True
    )

    @property
    def duration_human_readable(self):
        if self.duration:
            return get_human_readable_duration(str(self.duration)).lower()
        return None

    @property
    def duration_period_human_readable(self):
        if self.duration_period:
            return DurationPeriodChoices.get_choice(self.duration_period).label
        return None

    online_meeting_url = models.TextField(
        _('Online Meeting URL'),
        blank=True,
        default=''
    )

    validators = [PeriodActivityRegistrationDeadlineValidator]

    @property
    def activity_date(self):
        return self.deadline or self.start

    class Meta:
        verbose_name = _("Activity during a period")
        verbose_name_plural = _("Activities during a period")
        permissions = (
            ('api_read_periodactivity', 'Can view during a period activities through the API'),
            ('api_add_periodactivity', 'Can add during a period activities through the API'),
            ('api_change_periodactivity', 'Can change during a period activities through the API'),
            ('api_delete_periodactivity', 'Can delete during a period activities through the API'),

            ('api_read_own_periodactivity', 'Can view own during a period activities through the API'),
            ('api_add_own_periodactivity', 'Can add own during a period activities through the API'),
            ('api_change_own_periodactivity', 'Can change own during a period activities through the API'),
            ('api_delete_own_periodactivity', 'Can delete own during a period activities through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'activities/time-based/periods'

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        return u"{}/{}/initiatives/activities/details/time-based/period/{}/{}".format(
            domain, language,
            self.pk,
            self.slug
        )

    @property
    def required_fields(self):
        fields = super().required_fields
        if not self.is_online:
            fields.append('location')
        return fields + ['duration', 'is_online', 'duration_period']


class PeriodActivitySlot(ActivitySlot):
    activity = models.ForeignKey(PeriodActivity, related_name='slots', on_delete=models.CASCADE)
    start = models.DateTimeField(_('start date and time'), null=True, blank=True)
    end = models.DateTimeField(_('end date and time'), null=True, blank=True)

    class Meta:
        verbose_name = _('period activity slot')
        verbose_name_plural = _('period activity slots')
        permissions = (
            ('api_read_periodactivityslot', 'Can view over a period activity slots through the API'),
            ('api_add_periodactivityslot', 'Can add over a period activity slots through the API'),
            ('api_change_periodactivityslot', 'Can change over a period activity slots through the API'),
            ('api_delete_periodactivityslot', 'Can delete over a period activity slots through the API'),

            ('api_read_own_periodactivityslot', 'Can view own over a period activity slots through the API'),
            ('api_add_own_periodactivityslot', 'Can add own over a period activity slots through the API'),
            ('api_change_own_periodactivityslot', 'Can change own over a period activity slots through the API'),
            ('api_delete_own_periodactivityslot', 'Can delete own over a period activity slots through the API'),
        )


class TeamSlot(ActivitySlot):
    activity = models.ForeignKey(PeriodActivity, related_name='team_slots', on_delete=models.CASCADE)
    start = models.DateTimeField(_('start date and time'))
    duration = models.DurationField(_('duration'))
    team = models.OneToOneField(Team, related_name='slot', on_delete=models.CASCADE)

    @property
    def end(self):
        if self.start and self.duration:
            return self.start + self.duration

    @property
    def timezone(self):
        if self.start:
            return self.start.strftime("%Z %z")

    @property
    def is_complete(self):
        return self.start and self.duration

    class Meta:
        verbose_name = _('team slot')
        verbose_name_plural = _('team slots')
        permissions = (
            ('api_read_teamslot', 'Can view over a team slots through the API'),
            ('api_add_teamslot', 'Can add over a team slots through the API'),
            ('api_change_teamslot', 'Can change over a team slots through the API'),
            ('api_delete_teamslot', 'Can delete over a team slots through the API'),

            ('api_read_own_teamslot', 'Can view own over a team slots through the API'),
            ('api_add_own_teamslot', 'Can add own over a team slots through the API'),
            ('api_change_own_teamslot', 'Can change own over a team slots through the API'),
            ('api_delete_own_teamslot', 'Can delete own over a team slots through the API'),
        )

    def __str__(self):
        return str(_('Time slot for {}')).format(self.team)

    class JSONAPIMeta:
        resource_name = 'activities/time-based/team-slots'

    @property
    def accepted_participants(self):
        return self.team.members.filter(status='accepted')

    @property
    def event_data(self):
        if self.end < now() or self.status not in ['open', 'full']:
            return None
        title = self.activity.title
        if self.team.name:
            title += f" - {self.team.name}"
        location = ''
        if self.is_online:
            location = _('Anywhere/Online')
        elif self.location:
            location = self.location.locality
            if self.location_hint:
                location += f" {self.location_hint}"
        return {
            'uid': self.uid,
            'summary': title,
            'description': self.activity.description,
            'organizer': self.activity.owner.email,
            'url': self.activity.get_absolute_url(),
            'location': location,
            'start_time': self.start,
            'end_time': self.end,
        }


ONLINE_CHOICES = (
    (None, 'Not set yet'),
    (True, 'Yes, participants can join from anywhere or online'),
    (False, 'No, enter a location')
)


class RegistrationActivity(TimeBasedActivity):
    is_online = models.BooleanField(_('is online'), choices=ONLINE_CHOICES, null=True, default=None)

    location = models.ForeignKey(
        Geolocation, verbose_name=_('location'),
        null=True, blank=True, on_delete=models.SET_NULL
    )
    location_hint = models.TextField(_('location hint'), null=True, blank=True)

    start = models.DateField(
        _('Start date'),
        help_text=_('The first moment participants can start.'),
        null=True,
        blank=True
    )

    deadline = models.DateField(
        _('End date'),
        help_text=_('Participants can contribute until this date.'),
        null=True,
        blank=True
    )

    @property
    def duration_human_readable(self):
        if self.duration:
            return get_human_readable_duration(str(self.duration)).lower()
        return None

    online_meeting_url = models.TextField(
        _('Online Meeting URL'),
        blank=True,
        default=''
    )

    validators = [PeriodActivityRegistrationDeadlineValidator]

    @property
    def activity_date(self):
        return self.deadline or self.start

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        return self.url_pattern.format(
            domain, language,
            self.pk,
            self.slug
        )

    @property
    def required_fields(self):
        fields = super().required_fields
        if not self.is_online:
            fields.append("location")
        return fields + ["is_online"]

    @property
    def active_participants(self):
        return self.participants.filter(
            status__in=["new", "succeeded", "participating"]
        )

    @property
    def accepted_participants(self):
        return self.participants.filter(status__in=["succeeded"])

    class Meta:
        abstract = True


class DeadlineActivity(RegistrationActivity):
    url_pattern = "{}/{}/activities/details/deadline/{}/{}"

    duration = models.DurationField(
        _("Activity duration"),
        help_text=_("How much time will a participant contribute?"),
        null=True,
        blank=True,
    )

    @property
    def required_fields(self):
        return super().required_fields + ["duration"]

    class Meta:
        verbose_name = _("Flexible activity")
        verbose_name_plural = _("Flexible activities")

        permissions = (
            (
                "api_read_deadlineactivity",
                "Can view on a felxible activities through the API",
            ),
            (
                "api_add_deadlineactivity",
                "Can add on a felxible activities through the API",
            ),
            (
                "api_change_deadlineactivity",
                "Can change on a felxible activities through the API",
            ),
            (
                "api_delete_deadlineactivity",
                "Can delete on a felxible activities through the API",
            ),
            (
                "api_read_own_deadlineactivity",
                "Can view own on a felxible activities through the API",
            ),
            (
                "api_add_own_deadlineactivity",
                "Can add own on a felxible activities through the API",
            ),
            (
                "api_change_own_deadlineactivity",
                "Can change own on a felxible activities through the API",
            ),
            (
                "api_delete_own_deadlineactivity",
                "Can delete own on a felxible activities through the API",
            ),
        )

    class JSONAPIMeta:
        resource_name = "activities/time-based/deadlines"


class ScheduleActivity(RegistrationActivity):
    url_pattern = "{}/{}/activities/details/schedule/{}/{}"
    duration = models.DurationField(
        _("Activity duration"),
        help_text=_("How much time will a participant contribute?"),
        null=True,
        blank=True,
    )

    @property
    def accepted_participants(self):
        return self.registrations.filter(status__in=["accepted", "succeeded", "scheduled"])

    class Meta:
        verbose_name = _("Schedule activity")
        verbose_name_plural = _("Schedule activities")

        permissions = (
            ('api_read_scheduleactivity', 'Can view on a schedule activities through the API'),
            ('api_add_scheduleactivity', 'Can add on a schedule activities through the API'),
            ('api_change_scheduleactivity', 'Can change on a schedule activities through the API'),
            ('api_delete_scheduleactivity', 'Can delete on a schedule activities through the API'),

            ('api_read_own_scheduleactivity', 'Can view own on a schedule activities through the API'),
            ('api_add_own_scheduleactivity', 'Can add own on a schedule activities through the API'),
            ('api_change_own_scheduleactivity', 'Can change own on a schedule activities through the API'),
            ('api_delete_own_scheduleactivity', 'Can delete own on a schedule activities through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'activities/time-based/schedules'


class PeriodChoices(DjangoChoices):
    hours = ChoiceItem('hours', label=_("per hour"))  # TODO remove this after testing
    days = ChoiceItem('days', label=_("per day"))
    weeks = ChoiceItem('weeks', label=_("per week"))
    months = ChoiceItem('months', label=_("per month"))


class PeriodicActivity(RegistrationActivity):
    period = models.CharField(
        _('Period'),
        help_text=_('When should the activity be repeated?'),
        max_length=100,
        blank=True,
        null=True,
        choices=PeriodChoices,
    )
    duration = models.DurationField(
        _("Activity duration"),
        help_text=_("How much time will a participant contribute?"),
        null=True,
        blank=True,
    )
    url_pattern = "{}/{}/activities/details/periodic/{}/{}"

    @property
    def required_fields(self):
        return super().required_fields + ["duration", "period"]

    class Meta:
        verbose_name = _("Recurring activity")
        verbose_name_plural = _("Recurring activities")

        permissions = (
            (
                "api_read_periodicactivity",
                "Can view on a periodic activities through the API",
            ),
            (
                "api_add_periodicactivity",
                "Can add on a periodic activities through the API",
            ),
            (
                "api_change_periodicactivity",
                "Can change on a periodic activities through the API",
            ),
            (
                "api_delete_periodicactivity",
                "Can delete on a periodic activities through the API",
            ),
            (
                "api_read_own_periodicactivity",
                "Can view own on a periodic activities through the API",
            ),
            (
                "api_add_own_periodicactivity",
                "Can add own on a periodic activities through the API",
            ),
            (
                "api_change_own_periodicactivity",
                "Can change own on a periodic activities through the API",
            ),
            (
                "api_delete_own_periodicactivity",
                "Can delete own on a periodic activities through the API",
            ),
        )

    class JSONAPIMeta:
        resource_name = 'activities/time-based/periodics'


class Participant(Contributor):

    registration = models.ForeignKey(
        'time_based.Registration',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    @property
    def finished_contributions(self):
        return self.contributions.filter(
            timecontribution__end__lte=timezone.now()
        ).exclude(
            timecontribution__contribution_type=ContributionTypeChoices.preparation
        )

    @property
    def preparation_contributions(self):
        return self.contributions.filter(
            timecontribution__contribution_type=ContributionTypeChoices.preparation
        )

    @property
    def current_contribution(self):
        return self.contributions.get(status='new')

    @property
    def upcoming_contributions(self):
        return self.contributions.filter(start__gt=timezone.now())

    @property
    def started_contributions(self):
        return self.contributions.filter(start__lt=timezone.now())

    class Meta:
        abstract = True


class DateParticipant(Participant):
    motivation = models.TextField(blank=True, null=True)
    document = PrivateDocumentField(
        blank=True, null=True, view_name="date-participant-document"
    )

    class Meta:
        verbose_name = _("Participant to date activities")
        verbose_name_plural = _("Participants to date activities")
        permissions = (
            ("api_read_dateparticipant", "Can view participant through the API"),
            ("api_add_dateparticipant", "Can add participant through the API"),
            ("api_change_dateparticipant", "Can change participant through the API"),
            ("api_delete_dateparticipant", "Can delete participant through the API"),
            (
                "api_read_own_dateparticipant",
                "Can view own participant through the API",
            ),
            ("api_add_own_dateparticipant", "Can add own participant through the API"),
            (
                "api_change_own_dateparticipant",
                "Can change own participant through the API",
            ),
            (
                "api_delete_own_dateparticipant",
                "Can delete own participant through the API",
            ),
        )

    class JSONAPIMeta:
        resource_name = 'contributors/time-based/date-participants'


class PeriodParticipant(Participant, Contributor):
    motivation = models.TextField(blank=True, null=True)
    document = PrivateDocumentField(blank=True, null=True, view_name='period-participant-document')

    current_period = models.DateField(null=True, blank=True)

    class Meta():
        verbose_name = _("Participant during a period")
        verbose_name_plural = _("Participants during a period")
        permissions = (
            ('api_read_periodparticipant', 'Can view period participant through the API'),
            ('api_add_periodparticipant', 'Can add period participant through the API'),
            ('api_change_periodparticipant', 'Can change period participant through the API'),
            ('api_delete_periodparticipant', 'Can delete period participant through the API'),

            ('api_read_own_periodparticipant', 'Can view own period participant through the API'),
            ('api_add_own_periodparticipant', 'Can add own participant through the API'),
            ('api_change_own_periodparticipant', 'Can change own period participant through the API'),
            ('api_delete_own_periodparticipant', 'Can delete own period participant through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'contributors/time-based/period-participants'


class SlotParticipant(TriggerMixin, AnonymizationMixin, models.Model):

    slot = models.ForeignKey(
        DateActivitySlot, related_name='slot_participants', on_delete=models.CASCADE
    )
    participant = models.ForeignKey(
        DateParticipant, related_name='slot_participants', on_delete=models.CASCADE,
        blank=True, null=True
    )

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    status = models.CharField(max_length=40)
    auto_approve = True

    def __str__(self):
        return '{name} / {slot}'.format(name=self.participant.user, slot=self.slot)

    @property
    def user(self):
        return self.participant.user

    @property
    def activity(self):
        return self.slot.activity

    @property
    def calculated_status(self):
        if self.participant.status != 'accepted':
            return str(self.participant.states.current_state.name)
        return str(self.states.current_state.name)

    class Meta():
        verbose_name = _("Slot participant")
        verbose_name_plural = _("Slot participants")
        permissions = (
            ('api_read_slotparticipant', 'Can view slot participant through the API'),
            ('api_add_slotparticipant', 'Can add slot participant through the API'),
            ('api_change_slotparticipant', 'Can change slot participant through the API'),
            ('api_delete_slotparticipant', 'Can delete slot participant through the API'),

            ('api_read_own_slotparticipant', 'Can view own slot participant through the API'),
            ('api_add_own_slotparticipant', 'Can add own slot participant through the API'),
            ('api_change_own_slotparticipant', 'Can change own slot participant through the API'),
            ('api_delete_own_slotparticipant', 'Can delete own slot participant through the API'),
        )
        unique_together = ['slot', 'participant']
        ordering = ['slot__start']

    class JSONAPIMeta:
        resource_name = 'contributors/time-based/slot-participants'


class ContributionTypeChoices(DjangoChoices):
    date = ChoiceItem('date', label=_("activity on a date"))
    period = ChoiceItem('period', label=_("activity over a period"))
    preparation = ChoiceItem('preparation', label=_("preparation"))


class TimeContribution(Contribution):

    value = models.DurationField(_('value'))

    contribution_type = models.CharField(
        _('Contribution type'),
        max_length=20,
        blank=True,
        null=True,
        choices=ContributionTypeChoices.choices,
    )

    slot_participant = models.ForeignKey(
        SlotParticipant, null=True, blank=True, related_name='contributions', on_delete=models.SET_NULL
    )

    class JSONAPIMeta:
        resource_name = 'contributions/time-contribution'

    class Meta:
        verbose_name = _("Time contribution")
        verbose_name_plural = _("Contributions")

    def __str__(self):
        if self.contributor:
            return _("Contribution {name} {date}").format(
                name=self.contributor.user,
                date=self.start.date() if self.start else ''
            )
        return _("Contribution {date}").format(
            date=self.start.date() if self.start else ''
        )


class Skill(TranslatableModel):
    expertise = models.BooleanField(_('expertise based'),
                                    help_text=_('Is this skill expertise based, or could anyone do it?'),
                                    default=True)
    disabled = models.BooleanField(_('disabled'), default=False)

    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=100, ),
        description=models.TextField(_('description'), blank=True)
    )

    def __str__(self):
        return self.name

    class Meta():
        permissions = (
            ('api_read_skill', 'Can view skills through the API'),
        )
        verbose_name = _(u'Skill')
        verbose_name_plural = _(u'Skills')

    class JSONAPIMeta(object):
        resource_name = 'skills'


class Registration(TriggerMixin, PolymorphicModel):
    answer = models.TextField(blank=True, null=True)
    document = PrivateDocumentField(blank=True, null=True, view_name='registration-document')

    activity = models.ForeignKey(
        TimeBasedActivity,
        related_name='registrations',
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        'members.Member',
        related_name='registrations',
        on_delete=models.CASCADE
    )

    status = models.CharField(max_length=40)
    created = models.DateTimeField(default=timezone.now)

    @property
    def owner(self):
        return self.user

    @property
    def anonymized(self):
        return self.activity.anonymized

    def __str__(self):
        if self.activity_id:
            return _('Candidate {name} for {activity}').format(name=self.user, activity=self.activity)
        return _('Candidate {name}').format(name=self.user)

    class Meta:
        verbose_name = _("Candidate")
        verbose_name_plural = _("Candidates")


class DeadlineRegistration(Registration):
    class JSONAPIMeta(object):
        resource_name = 'contributors/time-based/deadline-registrations'

    @property
    def participants(self):
        return self.deadlineparticipant_set.all()

    class Meta:
        verbose_name = _("Candidate for flexible activities")
        verbose_name_plural = _("Candidates for flexible activities")

        permissions = (
            ("api_read_deadlineregistration", "Can view registration through the API"),
            ("api_add_deadlineregistration", "Can add registration through the API"),
            (
                "api_change_deadlineregistration",
                "Can change candidates through the API",
            ),
            (
                "api_delete_deadlineregistration",
                "Can delete candidates through the API",
            ),
            (
                "api_read_own_deadlineregistration",
                "Can view own candidates through the API",
            ),
            (
                "api_add_own_deadlineregistration",
                "Can add own candidates through the API",
            ),
            (
                "api_change_own_deadlineregistration",
                "Can change own candidates through the API",
            ),
            (
                "api_delete_own_deadlineregistration",
                "Can delete own candidates through the API",
            ),
        )


class ScheduleRegistration(Registration):
    class JSONAPIMeta(object):
        resource_name = 'contributors/time-based/schedule-registrations'

    @property
    def participants(self):
        return self.scheduleparticipant_set.all()

    class Meta:
        verbose_name = _("Candidate for schedule activities")
        verbose_name_plural = _("Candidates for schedule activities")

        permissions = (
            ("api_read_scheduleregistration", "Can view candidates through the API"),
            ("api_add_scheduleregistration", "Can add candidates through the API"),
            (
                "api_change_scheduleregistration",
                "Can change candidates through the API",
            ),
            (
                "api_delete_scheduleregistration",
                "Can delete candidates through the API",
            ),
            (
                "api_read_own_scheduleregistration",
                "Can view own candidates through the API",
            ),
            (
                "api_add_own_scheduleregistration",
                "Can add own candidates through the API",
            ),
            (
                "api_change_own_scheduleregistration",
                "Can change own candidates through the API",
            ),
            (
                "api_delete_own_scheduleregistration",
                "Can delete own candidates through the API",
            ),
        )


class PeriodicRegistration(Registration):
    class JSONAPIMeta(object):
        resource_name = 'contributors/time-based/periodic-registrations'

    @property
    def participants(self):
        return self.periodicparticipant_set.all()

    class Meta:
        verbose_name = _("Candidate for recurring activities")
        verbose_name_plural = _("Candidates for recurring activities")

        permissions = (
            (
                "api_read_periodicregistration",
                "Can view periodic candidates through the API",
            ),
            (
                "api_add_periodicregistration",
                "Can add periodic candidates through the API",
            ),
            (
                "api_change_periodicregistration",
                "Can change periodic candidates through the API",
            ),
            (
                "api_delete_periodicregistration",
                "Can delete periodic candidates through the API",
            ),
            (
                "api_read_own_periodicregistration",
                "Can view own periodic candidates through the API",
            ),
            (
                "api_add_own_periodicregistration",
                "Can add own periodic candidates through the API",
            ),
            (
                "api_change_own_periodicregistration",
                "Can change own periodic candidates through the API",
            ),
            (
                "api_delete_own_periodicregistration",
                "Can delete own periodic candidates through the API",
            ),
        )

    @property
    def first_slot(self):
        return self.participants.order_by("slot__start").first().slot

    @property
    def last_slot(self):
        return self.participants.order_by("slot__start").last().slot

    @property
    def total_hours(self):
        total = TimeContribution.objects.filter(
            contributor_id__in=self.participants.filter(
                status__in=["running", "new", "succeeded"]
            ).values_list("contributor_ptr_id", flat=True)
        ).aggregate(Sum("value"))
        return total["value__sum"]

    @property
    def total_slots(self):
        return self.participants.filter(
            status__in=["running", "new", "succeeded"]
        ).count()


class DeadlineParticipant(Participant, Contributor):
    class Meta:
        verbose_name = _("Participant to flexible activities")
        verbose_name_plural = _("Participants to flexible activities")

        permissions = (
            ("api_read_deadlineparticipant", "Can view participant through the API"),
            ("api_add_deadlineparticipant", "Can add participant through the API"),
            (
                "api_change_deadlineparticipant",
                "Can change participant through the API",
            ),
            (
                "api_delete_deadlineparticipant",
                "Can delete participant through the API",
            ),
            (
                "api_read_own_deadlineparticipant",
                "Can view own participant through the API",
            ),
            (
                "api_add_own_deadlineparticipant",
                "Can add own participant through the API",
            ),
            (
                "api_change_own_deadlineparticipant",
                "Can change own participant through the API",
            ),
            (
                "api_delete_own_deadlineparticipant",
                "Can delete own participant through the API",
            ),
        )

    class JSONAPIMeta(object):
        resource_name = 'contributors/time-based/deadline-participants'


class TeamScheduleRegistration(Registration):

    class JSONAPIMeta(object):
        resource_name = 'contributors/time-based/team-schedule-registrations'

    def __str__(self):
        if self.activity_id:
            return _('Regsitration Team {name} for {activity}').format(name=self.user, activity=self.activity)
        return _('Regsitration Team {name}').format(name=self.user)

    class Meta:
        verbose_name = _("Team for schedule activities")
        verbose_name_plural = _("Teams for schedule activities")

        permissions = (
            ("api_read_teamscheduleregistration", "Can view candidates through the API"),
            ("api_add_teamscheduleregistration", "Can add candidates through the API"),
            (
                "api_change_teamscheduleregistration",
                "Can change candidates through the API",
            ),
            (
                "api_delete_teamscheduleregistration",
                "Can delete candidates through the API",
            ),
            (
                "api_read_own_teamscheduleregistration",
                "Can view own candidates through the API",
            ),
            (
                "api_add_own_teamscheduleregistration",
                "Can add own candidates through the API",
            ),
            (
                "api_change_own_teamscheduleregistration",
                "Can change own candidates through the API",
            ),
            (
                "api_delete_own_teamscheduleregistration",
                "Can delete own candidates through the API",
            ),
        )


class Team(TriggerMixin, models.Model):
    invite_code = models.UUIDField(default=uuid.uuid4)

    registration = models.OneToOneField(
        Registration,
        related_name='team',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    activity = models.ForeignKey(
        Activity,
        related_name='teams',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    user = models.ForeignKey(
        'members.Member',
        verbose_name=_('Team captain'),
        related_name='team_captains',
        on_delete=models.CASCADE
    )

    status = models.CharField(max_length=40)
    created = models.DateTimeField(default=timezone.now)

    @property
    def owner(self):
        return self.user

    class JSONAPIMeta(object):
        resource_name = 'teams/teams'

    def __str__(self):
        return _('Team {name}').format(name=self.user.full_name)


class TeamMember(TriggerMixin, models.Model):
    team = models.ForeignKey(
        'time_based.Team',
        related_name='team_members',
        on_delete=models.CASCADE,
    )

    user = models.ForeignKey(
        'members.Member',
        related_name='team_members',
        on_delete=models.CASCADE
    )

    status = models.CharField(max_length=40)
    created = models.DateTimeField(default=timezone.now)

    class JSONAPIMeta(object):
        resource_name = 'teams/team-members'

    def __str__(self):
        return _('Team member {name}').format(name=self.user.full_name)


class ScheduleParticipant(Participant, Contributor):
    registration = models.ForeignKey(
        'time_based.ScheduleRegistration',
        related_name='participants',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    slot = models.ForeignKey(
        "time_based.ScheduleSlot",
        related_name="participants",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Participant to schedule activities")
        verbose_name_plural = _("Participants to schedule activities")

        permissions = (
            ("api_read_scheduleparticipant", "Can view participant through the API"),
            ("api_add_scheduleparticipant", "Can add participant through the API"),
            (
                "api_change_scheduleparticipant",
                "Can change participant through the API",
            ),
            (
                "api_delete_scheduleparticipant",
                "Can delete participant through the API",
            ),
            (
                "api_read_own_scheduleparticipant",
                "Can view own participant through the API",
            ),
            (
                "api_add_own_scheduleparticipant",
                "Can add own participant through the API",
            ),
            (
                "api_change_own_scheduleparticipant",
                "Can change own participant through the API",
            ),
            (
                "api_delete_own_scheduleparticipant",
                "Can delete own participant through the API",
            ),
        )

    class JSONAPIMeta(object):
        resource_name = 'contributors/time-based/schedule-participants'


class TeamScheduleParticipant(Participant, Contributor):

    registration = models.ForeignKey(
        'time_based.TeamScheduleRegistration',
        related_name='participants',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    team_member = models.ForeignKey(
        'time_based.TeamMember',
        related_name='participations',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    slot = models.ForeignKey(
        "time_based.TeamScheduleSlot",
        related_name="participants",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Team member participation")
        verbose_name_plural = _("Team member participations")

        permissions = (
            (
                "api_read_teamscheduleparticipant",
                "Can view team member participant through the API"
            ),
            (
                "api_add_teamscheduleparticipant",
                "Can add team member participant through the API"
            ),
            (
                "api_change_teamscheduleparticipant",
                "Can change team member participant through the API",
            ),
            (
                "api_delete_teamscheduleparticipant",
                "Can delete team member participant through the API",
            ),
            (
                "api_read_own_teamscheduleparticipant",
                "Can view own team member participant through the API",
            ),
            (
                "api_add_own_teamscheduleparticipant",
                "Can add own team member participant through the API",
            ),
            (
                "api_change_own_teamscheduleparticipant",
                "Can change own team member participant through the API",
            ),
            (
                "api_delete_own_scheduleparticipant",
                "Can delete own participant through the API",
            ),
        )

    class JSONAPIMeta(object):
        resource_name = 'contributors/time-based/team-schedule-participants'


class Slot(models.Model):
    status = models.CharField(max_length=40)
    start = models.DateTimeField(_('start date and time'), null=True, blank=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def uid(self):
        return "{}-{}-{}".format(connection.tenant.client_name, "dateactivity", self.pk)

    @property
    def google_calendar_link(self):
        def format_date(date):
            if date:
                return date.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        details = self.activity.details
        if self.is_online and self.online_meeting_url:
            details += _("\nJoin: {url}").format(url=self.online_meeting_url)

        url = "https://calendar.google.com/calendar/render"
        params = {
            "action": "TEMPLATE",
            "text": self.activity.title,
            "dates": "{}/{}".format(
                format_date(self.start), format_date(self.start + self.duration)
            ),
            "details": details,
            "uid": self.uid,
        }

        if self.location:
            params["location"] = self.location.formatted_address
            if self.location_hint:
                params["location"] = f'{params["location"]} ({self.location_hint})'

        return "{}?{}".format(url, urlencode(params))


class PeriodicSlot(TriggerMixin, Slot):
    activity = models.ForeignKey(
        PeriodicActivity, on_delete=models.CASCADE, related_name="slots"
    )

    duration = models.DurationField(_("duration"), null=True, blank=True)
    end = models.DateTimeField(_('end date and time'), null=True, blank=True)

    @property
    def accepted_participants(self):
        return self.participants.filter(
            status__in=["accepted", "participating", "succeeded", "new"],
            registration__status='accepted'
        )


class BaseScheduleSlot(TriggerMixin, Slot):
    start = models.DateTimeField(_('start date and time'), null=True, blank=True)

    duration = models.DurationField(_("duration"), null=True, blank=True)

    is_online = models.BooleanField(
        _("is online"), choices=DateActivity.ONLINE_CHOICES, null=True, default=None
    )

    online_meeting_url = models.TextField(
        _("online meeting link"), blank=True, default=""
    )

    location = models.ForeignKey(
        Geolocation,
        verbose_name=_("location"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    location_hint = models.TextField(_("location hint"), null=True, blank=True)

    @property
    def end(self):
        if self.duration and self.start:
            return self.start + self.duration

    def __str__(self):
        start = self.start.strftime("%Y-%m-%d %H:%M") if self.start else self.id
        return str(_(f'Slot {start}'))

    class Meta:
        abstract = True


class ScheduleSlot(BaseScheduleSlot):
    activity = models.ForeignKey(
        ScheduleActivity, on_delete=models.CASCADE, related_name="slots"
    )

    @property
    def accepted_participants(self):
        return self.participants.filter(
            status__in=["accepted", "participating", "succeeded", "new"],
        )


class TeamScheduleSlot(BaseScheduleSlot):
    activity = models.ForeignKey(
        ScheduleActivity, on_delete=models.CASCADE, related_name="team_slots"
    )

    team = models.ForeignKey(
        'time_based.Team',
        related_name='slots',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class JSONAPIMeta:
        resource_name = "activities/time-based/team-schedule-slots"

    @property
    def accepted_participants(self):
        return self.participants.filter(
            status__in=["accepted", "participating", "succeeded", "new"],
            team_member__status__in=['accepted', 'new']
        )


class PeriodicParticipant(Participant, Contributor):
    slot = models.ForeignKey(
        PeriodicSlot, on_delete=models.CASCADE, related_name="participants"
    )

    class Meta:
        verbose_name = _("Participant to ecurring activities")
        verbose_name_plural = _("Participants to recurring activities")

        permissions = (
            (
                "api_read_periodicparticipant",
                "Can view recurring participant through the API",
            ),
            (
                "api_add_periodicparticipant",
                "Can add recurring participant through the API",
            ),
            (
                "api_change_periodicparticipant",
                "Can change recurring participant through the API",
            ),
            (
                "api_delete_periodicparticipant",
                "Can delete recurring participant through the API",
            ),
            (
                "api_read_own_periodicparticipant",
                "Can view own recurring participant through the API",
            ),
            (
                "api_add_own_periodicparticipant",
                "Can add own recurring participant through the API",
            ),
            (
                "api_change_own_periodicparticipant",
                "Can change own recurring participant through the API",
            ),
            (
                "api_delete_own_periodicparticipant",
                "Can delete own recurring participant through the API",
            ),
        )

    class JSONAPIMeta(object):
        resource_name = "contributors/time-based/periodic-participants"


from bluebottle.time_based.periodic_tasks import *  # noqa
from bluebottle.time_based.signals import *  # noqa
