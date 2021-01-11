from html.parser import HTMLParser
from urllib.parse import urlencode

import pytz
from django.db import models, connection
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import DjangoChoices, ChoiceItem
from timezonefinder import TimezoneFinder

from bluebottle.activities.models import Activity, Contributor, Contribution
from bluebottle.files.fields import PrivateDocumentField
from bluebottle.fsm.triggers import TriggerMixin
from bluebottle.geo.models import Geolocation
from bluebottle.time_based.validators import (
    PeriodActivityRegistrationDeadlineValidator, DateActivityRegistrationDeadlineValidator, CompletedSlotsValidator,
    HasSlotValidator
)
from bluebottle.utils.models import ValidatedModelMixin, AnonymizationMixin

tf = TimezoneFinder()


class TimeBasedActivity(Activity):
    ONLINE_CHOICES = (
        (None, 'Not set yet'),
        (True, 'Yes, participants can join from anywhere or online'),
        (False, 'No, enter a location')
    )
    capacity = models.PositiveIntegerField(_('attendee limit'), null=True, blank=True)

    is_online = models.NullBooleanField(_('is online'), choices=ONLINE_CHOICES, null=True, default=None)
    location = models.ForeignKey(Geolocation, verbose_name=_('location'),
                                 null=True, blank=True, on_delete=models.SET_NULL)
    location_hint = models.TextField(_('location hint'), null=True, blank=True)

    registration_deadline = models.DateField(
        _('registration deadline'),
        null=True,
        blank=True
    )

    expertise = models.ForeignKey(
        'tasks.Skill',
        verbose_name=_('skill'),
        blank=True,
        null=True
    )

    review = models.NullBooleanField(_('review participants'), null=True, default=None)

    preparation = models.DurationField(
        _('Preparation time'),
        null=True, blank=True,
    )

    @property
    def required_fields(self):
        fields = ['title', 'description', 'review', ]
        return fields

    @property
    def participants(self):
        return self.contributors.instance_of(PeriodParticipant, DateParticipant)

    @property
    def cancelled_participants(self):
        return self.participants.filter(status='cancelled')

    @property
    def active_participants(self):
        return self.participants.filter(status__in=('accepted', 'new'))

    @property
    def accepted_participants(self):
        return self.participants.filter(status__in=('accepted', 'succeeded'))

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
    def details(self):
        details = HTMLParser().unescape(
            u'{}\n{}'.format(
                strip_tags(self.description), self.get_absolute_url()
            )
        )

        if self.is_online and self.online_meeting_url:
            details += _('\nJoin: {url}').format(url=self.online_meeting_url)

        return details

    @property
    def google_calendar_link(self):
        def format_date(date):
            if date:
                return date.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

        url = u'https://calendar.google.com/calendar/render'
        params = {
            'action': u'TEMPLATE',
            'text': self.title,
            'dates': u'{}/{}'.format(
                format_date(self.start), format_date(self.start + self.duration)
            ),
            'details': self.details,
            'uid': self.uid,
        }

        if self.location:
            params['location'] = self.location.formatted_address

        return u'{}?{}'.format(url, urlencode(params))

    @property
    def outlook_link(self):
        def format_date(date):
            if date:
                return date.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

        url = 'https://outlook.live.com/owa/'

        params = {
            'rru': 'addevent',
            'path': '/calendar/action/compose&rru=addevent',
            'allday': False,
            'subject': self.title,
            'startdt': format_date(self.start),
            'enddt': format_date(self.start + self.duration),
            'body': self.details
        }

        if self.location:
            params['location'] = self.location.formatted_address

        return u'{}?{}'.format(url, urlencode(params))


class SlotSelectionChoices(DjangoChoices):
    all = ChoiceItem('all', label=_("All"))
    free = ChoiceItem('free', label=_("Free"))


class DateActivity(TimeBasedActivity):
    start = models.DateTimeField(_('start date and time'), null=True, blank=True)
    duration = models.DurationField(_('duration'), null=True, blank=True)

    online_meeting_url = models.TextField(
        _('online meeting link'),
        blank=True, default=''
    )

    slot_selection = models.CharField(
        _('Slot selection'),
        help_text=_(
            'All: Participant will join all time slots. '
            'Free: Participant can pick any number of slots to join.'),
        max_length=20,
        blank=True,
        null=True,
        default=SlotSelectionChoices.all,
        choices=SlotSelectionChoices.choices,
    )

    duration_period = 'overall'

    validators = [
        DateActivityRegistrationDeadlineValidator,
        CompletedSlotsValidator,
        HasSlotValidator
    ]

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

    @property
    def activity_date(self):
        return self.start

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

    class Meta:
        abstract = True


class DateActivitySlot(ActivitySlot):
    activity = models.ForeignKey(DateActivity, related_name='slots')

    start = models.DateTimeField(_('start date and time'), null=True, blank=True)
    duration = models.DurationField(_('duration'), null=True, blank=True)
    is_online = models.NullBooleanField(
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
    def required_fields(self):
        fields = [
            'start', 'duration', 'is_online'
        ]
        if not self.is_online:
            fields.append('location')
        return fields

    @property
    def end(self):
        return self.start + self.duration

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
        return self.title or "Slot ID {}".format(self.id)

    class Meta:
        verbose_name = _('slot')
        verbose_name_plural = _('slots')


class DurationPeriodChoices(DjangoChoices):
    overall = ChoiceItem('overall', label=_("in total"))
    days = ChoiceItem('days', label=_("per day"))
    weeks = ChoiceItem('weeks', label=_("per week"))
    months = ChoiceItem('months', label=_("per month"))


class PeriodActivity(TimeBasedActivity):
    start = models.DateField(
        _('Start date'),
        null=True,
        blank=True
    )

    deadline = models.DateField(
        _('End date'),
        null=True,
        blank=True
    )

    duration = models.DurationField(
        _('Time per period'),
        null=True,
        blank=True
    )

    duration_period = models.CharField(
        _('period'),
        max_length=20,
        blank=True,
        null=True,
        choices=DurationPeriodChoices.choices,
    )

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

    @property
    def required_fields(self):
        fields = super().required_fields
        if not self.is_online:
            fields.append('location')
        return fields + ['duration', 'is_online', 'duration_period']


class PeriodActivitySlot(ActivitySlot):
    activity = models.ForeignKey(PeriodActivity, related_name='slots')
    start = models.DateTimeField(_('start date and time'), null=True, blank=True)
    end = models.DateTimeField(_('end date and time'), null=True, blank=True)


class Participant(Contributor):

    @property
    def finished_contributions(self):
        return self.contributions.filter(
            timecontribution__end__lte=timezone.now()
        )

    class Meta:
        abstract = True


class DateParticipant(Participant):
    motivation = models.TextField(blank=True, null=True)
    document = PrivateDocumentField(blank=True, null=True)

    class Meta(object):
        verbose_name = _("Participant on a date")
        verbose_name_plural = _("Participants on a date")
        permissions = (
            ('api_read_dateparticipant', 'Can view participant through the API'),
            ('api_add_dateparticipant', 'Can add participant through the API'),
            ('api_change_dateparticipant', 'Can change participant through the API'),
            ('api_delete_dateparticipant', 'Can delete participant through the API'),

            ('api_read_own_dateparticipant', 'Can view own participant through the API'),
            ('api_add_own_dateparticipant', 'Can add own participant through the API'),
            ('api_change_own_dateparticipant', 'Can change own participant through the API'),
            ('api_delete_own_dateparticipant', 'Can delete own participant through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'contributors/time-based/date-participants'


class PeriodParticipant(Participant, Contributor):
    motivation = models.TextField(blank=True, null=True)
    document = PrivateDocumentField(blank=True, null=True)

    current_period = models.DateField(null=True, blank=True)

    class Meta(object):
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

    @property
    def current_contribution(self):
        return self.contributions.get(status='new')

    @property
    def finished_contributions(self):
        return self.contributions.filter(end__lt=timezone.now())

    class JSONAPIMeta:
        resource_name = 'contributors/time-based/period-participants'


class SlotParticipant(TriggerMixin, models.Model):

    slot = models.ForeignKey(DateActivitySlot)
    participant = models.ForeignKey(DateParticipant)

    @property
    def user(self):
        return self.participant.user

    class Meta(object):
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

    class JSONAPIMeta:
        resource_name = 'contributors/time-based/slot-participants'


class TimeContribution(Contribution):
    value = models.DurationField(_('value'))

    slot_participant = models.ForeignKey(SlotParticipant, null=True)

    class Meta:
        verbose_name = _("Time contribution")
        verbose_name_plural = _("Contributions")

    def __str__(self):
        return _("Contribution {name} {date}").format(
            name=self.contributor.user,
            date=self.start.date() if self.start else ''
        )


from bluebottle.time_based.periodic_tasks import *  # noqa
