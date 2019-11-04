import datetime

from django.db import models
from django.db.models import Count, Sum
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import get_current_timezone

from bluebottle.activities.models import Activity, Contribution
from bluebottle.events.transitions import EventTransitions, ParticipantTransitions
from bluebottle.follow.models import follow
from bluebottle.fsm import TransitionManager
from bluebottle.geo.models import Geolocation
from bluebottle.utils.models import Validator


class RegistrationDeadlineValidator(Validator):
    field = 'registration_deadline'
    code = 'registration-deadline'
    message = _('Registration deadline should be before the start time'),

    def is_valid(self):
        return (
            not self.instance.registration_deadline or (
                self.instance.start_date and
                self.instance.registration_deadline < self.instance.start_date
            )
        )


class Event(Activity):
    capacity = models.PositiveIntegerField(_('attendee limit'), null=True, blank=True)
    automatically_accept = models.BooleanField(default=True)

    is_online = models.NullBooleanField(_('is online'), null=True, default=None)
    location = models.ForeignKey(Geolocation, verbose_name=_('location'),
                                 null=True, blank=True, on_delete=models.SET_NULL)
    location_hint = models.TextField(_('location hint'), null=True, blank=True)

    start_date = models.DateField(_('start date'), null=True, blank=True)
    start_time = models.TimeField(_('start time'), null=True, blank=True)
    duration = models.FloatField(_('duration'), null=True, blank=True)
    end = models.DateTimeField(_('end'), null=True, blank=True)
    registration_deadline = models.DateField(_('deadline to apply'), null=True, blank=True)

    transitions = TransitionManager(EventTransitions, 'status')

    validators = [RegistrationDeadlineValidator]

    @property
    def required_fields(self):
        fields = ['title', 'description', 'start_date', 'start_time', 'duration', 'is_online', ]

        if not self.is_online:
            fields.append('location')

        return fields

    @property
    def stats(self):
        stats = self.contributions.filter(
            status=ParticipantTransitions.values.succeeded).\
            aggregate(count=Count('user__id'), hours=Sum('participant__time_spent'))
        committed = self.contributions.filter(
            status=ParticipantTransitions.values.new).\
            aggregate(committed_count=Count('user__id'), committed_hours=Sum('participant__time_spent'))
        stats.update(committed)
        return stats

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        permissions = (
            ('api_read_event', 'Can view event through the API'),
            ('api_add_event', 'Can add event through the API'),
            ('api_change_event', 'Can change event through the API'),
            ('api_delete_event', 'Can delete event through the API'),

            ('api_read_own_event', 'Can view own event through the API'),
            ('api_add_own_event', 'Can add own event through the API'),
            ('api_change_own_event', 'Can change own event through the API'),
            ('api_delete_own_event', 'Can delete own event through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'activities/events'

    def check_capacity(self):
        if self.capacity and len(self.participants) >= self.capacity and self.status == EventTransitions.values.open:
            self.transitions.full()
            self.save()
        elif self.capacity and len(self.participants) < self.capacity and self.status == EventTransitions.values.full:
            self.transitions.reopen()

    @property
    def start(self):
        if self.start_time and self.start_date:
            return datetime.datetime.combine(
                self.start_date,
                self.start_time.replace(tzinfo=get_current_timezone())
            )

    def save(self, *args, **kwargs):
        if self.start and self.duration:
            self.end = self.start + datetime.timedelta(hours=self.duration)
        return super(Event, self).save(*args, **kwargs)

    @property
    def participants(self):
        return self.contributions.filter(
            status__in=[ParticipantTransitions.values.new,
                        ParticipantTransitions.values.succeeded]
        )


class Participant(Contribution):
    time_spent = models.FloatField(default=0)
    transitions = TransitionManager(ParticipantTransitions, 'status')

    class Meta:
        verbose_name = _("Participant")
        verbose_name_plural = _("Participants")

        permissions = (
            ('api_read_participant', 'Can view participant through the API'),
            ('api_add_participant', 'Can add participant through the API'),
            ('api_change_participant', 'Can change participant through the API'),
            ('api_delete_participant', 'Can delete participant through the API'),

            ('api_read_own_participant', 'Can view own participant through the API'),
            ('api_add_own_participant', 'Can add own participant through the API'),
            ('api_change_own_participant', 'Can change own participant through the API'),
            ('api_delete_own_participant', 'Can delete own participant through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'contributions/participants'

    def save(self, *args, **kwargs):
        created = self.pk is None

        super(Participant, self).save(*args, **kwargs)

        if created and self.status == 'new':
            self.transitions.initiate()
            follow(self.user, self.activity)

        self.activity.check_capacity()

from bluebottle.events.signals import *  # noqa
