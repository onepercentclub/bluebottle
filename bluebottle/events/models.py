from django.db import models
from django.forms.models import model_to_dict

from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

from djchoices.choices import ChoiceItem

from bluebottle.fsm import TransitionNotAllowed
from bluebottle.events.messages import EventDoneOwnerMessage, EventClosedOwnerMessage
from bluebottle.follow.models import follow, unfollow
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

    start_time = models.DateTimeField(_('start'))
    end_time = models.DateTimeField(_('end'))
    registration_deadline = models.DateTimeField(_('registration deadline'))

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
        resource_name = 'events'

    def save(self, *args, **kwargs):
        if self.status == Activity.Status.draft:
            try:
                self.open()
            except TransitionNotAllowed:
                pass

        super(Event, self).save(*args, **kwargs)

    def check_capacity(self):
        if len(self.participants) >= self.capacity and self.status == Event.Status.open:
            self.full()
            self.save()
        elif len(self.participants) < self.capacity and self.status == Event.Status.full:
            self.reopen()

    @property
    def duration(self):
        return (self.start_time - self.end_time).seconds / 60

    @property
    def participants(self):
        return self.contributions.filter(status=Participant.Status.new)

    def can_start(self):
        if not self.start_time:
            return _('Start date has not been set')
        if self.start_time > now():
            return _('The start date has not passed')

    def can_open(self):
        if not self.start_time:
            return _('Start date has not been set')
        if self.start_time < now():
            return _('The start date has passed')

    def can_end(self):
        if not self.end_time:
            return _('End date has not been set')
        if not self.end_time < now():
            return _('The end date has not passed')

    def is_complete(self):
        from bluebottle.events.serializers import EventSubmitSerializer
        serializer = EventSubmitSerializer(
            data=model_to_dict(self)
        )
        if not serializer.is_valid():
            return _('Please make sure all required fields are filled in')

    def initiative_is_approved(self):
        if not self.initiative.status == 'approved':
            return _('Please make sure the initiative is approved')

    @Activity.status.transition(
        source=Activity.Status.draft,
        target=Activity.Status.open,
        serializer='bluebottle.events.serializers.EventSubmitSerializer',
        conditions=[is_complete, initiative_is_approved]
    )
    def open(self):
        pass

    @Activity.status.transition(
        source=Activity.Status.open,
        target=Activity.Status.full,
        conditions=[can_open]
    )
    def full(self):
        pass

    @Activity.status.transition(
        source=Activity.Status.full,
        target=Activity.Status.open,
        conditions=[can_open]
    )
    def reopen(self):
        pass

    @Activity.status.transition(
        source=Activity.Status.closed,
        target=Activity.Status.draft,
    )
    def redraft(self, **kwargs):
        pass

    @Activity.status.transition(
        source=[Activity.Status.full, Activity.Status.open],
        target=Activity.Status.running,
        conditions=[can_start]
    )
    def start(self, **kwargs):
        pass

    @Activity.status.transition(
        source=Activity.Status.running,
        target=Activity.Status.done,
        conditions=[can_end],
        messages=[EventDoneOwnerMessage]
    )
    def done(self):
        for member in self.participants:
            member.success()
            member.save()

    @Activity.status.transition(
        source='*',
        target=Activity.Status.closed,
        messages=[EventClosedOwnerMessage]
    )
    def close(self):
        pass

    @Activity.status.transition(
        source=Activity.Status.closed,
        target=Activity.Status.open,
        conditions=[can_open]
    )
    def extend(self):
        pass


class Participant(Contribution):
    class Status(Contribution.Status):
        withdrawn = ChoiceItem('withdrawn', _('withdrawn'))
        rejected = ChoiceItem('rejected', _('rejected'))
        no_show = ChoiceItem('no_show', _('no_show'))
        closed = ChoiceItem('closed', _('closed'))

    time_spent = models.FloatField(default=0)

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

    def event_is_open(self):
        if not self.activity.status == Activity.Status.open:
            return _('The event is not open')

    def event_is_open_or_full(self):
        if self.activity.status not in (Activity.Status.open, Activity.Status.full):
            return _('The event is not open or full')

    def save(self, *args, **kwargs):
        created = self.pk is None

        super(Participant, self).save(*args, **kwargs)

        if created:
            follow(self.user, self.activity)

        self.activity.check_capacity()

    @Contribution.status.transition(
        source=Status.new,
        target=Status.withdrawn,
        conditions=[event_is_open_or_full]
    )
    def withdraw(self):
        unfollow(self.user, self.activity)

    @Contribution.status.transition(
        source=Status.withdrawn,
        target=Status.new,
        conditions=[event_is_open_or_full]
    )
    def reapply(self):
        follow(self.user, self.activity)

    @Contribution.status.transition(
        source=[Status.new],
        target=Status.rejected,
        permission=Contribution.is_activity_manager
    )
    def reject(self):
        unfollow(self.user, self.activity)

    @Contribution.status.transition(
        source=[Status.new, Status.no_show, Status.rejected, Status.withdrawn],
        target=Status.success,
    )
    def success(self):
        follow(self.user, self.activity)
        self.time_spent = self.activity.duration

    @Contribution.status.transition(
        source=Status.success,
        target=Status.no_show,
        permission=Contribution.is_activity_manager
    )
    def no_show(self):
        unfollow(self.user, self.activity)
        self.time_spent = None

    @Contribution.status.transition(
        source='*',
        target=Status.closed,
    )
    def close(self):
        self.time_spent = None
