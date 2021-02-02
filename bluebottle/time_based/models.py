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
    PeriodActivityRegistrationDeadlineValidator, CompletedSlotsValidator,
    HasSlotValidator
)
from bluebottle.utils.models import ValidatedModelMixin, AnonymizationMixin
from bluebottle.utils.utils import get_current_host, get_current_language


tf = TimezoneFinder()


class TimeBasedActivity(Activity):
    ONLINE_CHOICES = (
        (None, 'Not set yet'),
        (True, 'Yes, anywhere/online'),
        (False, 'No, enter a location')
    )
    capacity = models.PositiveIntegerField(_('attendee limit'), null=True, blank=True)

    old_is_online = models.NullBooleanField(
        _('is online'),
        db_column='is_online',
        choices=ONLINE_CHOICES,
        null=True, default=None)
    old_location = models.ForeignKey(
        Geolocation,
        db_column='location_id',
        verbose_name=_('location'),
        null=True, blank=True, on_delete=models.SET_NULL)
    old_location_hint = models.TextField(
        _('location hint'),
        db_column='location_hint',
        null=True, blank=True)

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
    def details(self):
        details = HTMLParser().unescape(
            u'{}\n{}'.format(
                strip_tags(self.description), self.get_absolute_url()
            )
        )
        return details


class SlotSelectionChoices(DjangoChoices):
    all = ChoiceItem('all', label=_("All"))
    free = ChoiceItem('free', label=_("Free"))


class DateActivity(TimeBasedActivity):

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

    old_online_meeting_url = models.TextField(
        _('online meeting link'),
        blank=True, default=''
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
        return self.slots.filter(status__in=['open', 'full', 'running'])

    @property
    def google_calendar_link(self):
        def format_date(date):
            if date:
                return date.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

        if self.active_slots.count() == 1:
            slot = self.active_slots.first()
            url = u'https://calendar.google.com/calendar/render'
            params = {
                'action': u'TEMPLATE',
                'text': self.title,
                'dates': u'{}/{}'.format(
                    format_date(slot.start), format_date(slot.start + slot.duration)
                ),
                'details': self.details,
                'uid': slot.uid,
            }

            if slot.location:
                params['location'] = slot.location.formatted_address

            return u'{}?{}'.format(url, urlencode(params))
        raise NotImplementedError("Can't create calendar link with multiple dates.")

    @property
    def outlook_link(self):
        def format_date(date):
            if date:
                return date.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
        if self.active_slots.count() == 1:
            slot = self.active_slots.first()

            url = 'https://outlook.live.com/owa/'

            params = {
                'rru': 'addevent',
                'path': '/calendar/action/compose&rru=addevent',
                'allday': False,
                'subject': self.title,
                'startdt': format_date(slot.start),
                'enddt': format_date(slot.start + slot.duration),
                'body': self.details
            }

            if slot.location:
                params['location'] = slot.location.formatted_address
            return u'{}?{}'.format(url, urlencode(params))
        raise NotImplementedError("Can't create calendar link with multiple dates.")

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
        return u"{}/{}/initiatives/activities/details/time-based/date/{}/{}".format(
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

    @property
    def uid(self):
        return '{}-{}-{}'.format(connection.tenant.client_name, 'dateactivityslot', self.pk)

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

        url = u'https://calendar.google.com/calendar/render'
        params = {
            'action': u'TEMPLATE',
            'text': self.activity.title,
            'dates': u'{}/{}'.format(
                format_date(self.start), format_date(self.start + self.duration)
            ),
            'details': self.activity.details,
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
            'subject': self.activity.title,
            'startdt': format_date(self.start),
            'enddt': format_date(self.start + self.duration),
            'body': self.activity.details
        }

        if self.location:
            params['location'] = self.location.formatted_address

        return u'{}?{}'.format(url, urlencode(params))

    @property
    def accepted_participants(self):
        return self.slot_participants.filter(status='registered', participant__status='accepted')

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
            'start',
            'duration'
        ]
        if not self.is_online:
            fields.append('location')
        return fields

    @property
    def end(self):
        if self.start and self.duration:
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

    is_online = models.NullBooleanField(_('is online'), choices=ONLINE_CHOICES, null=True, default=None)
    location = models.ForeignKey(Geolocation, verbose_name=_('location'),
                                 null=True, blank=True, on_delete=models.SET_NULL)
    location_hint = models.TextField(_('location hint'), null=True, blank=True)

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
    activity = models.ForeignKey(PeriodActivity, related_name='slots')
    start = models.DateTimeField(_('start date and time'), null=True, blank=True)
    end = models.DateTimeField(_('end date and time'), null=True, blank=True)

    class Meta:
        verbose_name = _('slot')
        verbose_name_plural = _('slots')
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

    slot = models.ForeignKey(DateActivitySlot, related_name='slot_participants')
    participant = models.ForeignKey(DateParticipant, related_name='slot_participants')

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
        unique_together = ['slot', 'participant']

    class JSONAPIMeta:
        resource_name = 'contributors/time-based/slot-participants'


class TimeContribution(Contribution):
    value = models.DurationField(_('value'))

    slot_participant = models.ForeignKey(SlotParticipant, null=True, related_name='contributions')

    class Meta:
        verbose_name = _("Time contribution")
        verbose_name_plural = _("Contributions")

    def __str__(self):
        return _("Contribution {name} {date}").format(
            name=self.contributor.user,
            date=self.start.date() if self.start else ''
        )


from bluebottle.time_based.periodic_tasks import *  # noqa
