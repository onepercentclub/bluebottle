from django.db import models

from django.utils.translation import ugettext_lazy as _

from bluebottle.follow.models import follow
from bluebottle.fsm import TransitionNotAllowed, TransitionManager
from bluebottle.events.transitions import EventTransitions, ParticipantTransitions
from bluebottle.activities.models import Activity, Contribution
from bluebottle.geo.models import Geolocation


from .tasks import *  # noqa


class Event(Activity):
    capacity = models.PositiveIntegerField(null=True, blank=True)
    automatically_accept = models.BooleanField(default=True)

    is_online = models.NullBooleanField(null=True, default=None)
    location = models.ForeignKey(Geolocation, verbose_name=_('location'),
                                 null=True, blank=True, on_delete=models.SET_NULL)
    location_hint = models.TextField(_('location hint'), null=True, blank=True)

    start_time = models.DateTimeField(_('start'), null=True, blank=True)
    end_time = models.DateTimeField(_('end'), null=True, blank=True)
    registration_deadline = models.DateTimeField(_('registration deadline'), null=True, blank=True)

    transitions = TransitionManager(EventTransitions, 'status')

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

    def save(self, *args, **kwargs):
        if self.status == EventTransitions.values.draft:
            try:
                self.transitions.open()
            except TransitionNotAllowed:
                pass

        super(Event, self).save(*args, **kwargs)

    def check_capacity(self):
        if len(self.participants) >= self.capacity and self.status == EventTransitions.values.open:
            self.transitions.full()
            self.save()
        elif len(self.participants) < self.capacity and self.status == EventTransitions.values.full:
            self.transitions.reopen()

    @property
    def duration(self):
        return (self.end_time - self.start_time).seconds / 60

    @property
    def participants(self):
        return self.contributions.filter(
            status__in=[ParticipantTransitions.values.new,
                        ParticipantTransitions.values.success]
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
        resource_name = 'participants'

    def save(self, *args, **kwargs):
        created = self.pk is None

        super(Participant, self).save(*args, **kwargs)

        if created:
            follow(self.user, self.activity)

        self.activity.check_capacity()
