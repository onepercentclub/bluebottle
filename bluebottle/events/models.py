from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from djchoices.choices import ChoiceItem

from bluebottle.follow.models import follow, unfollow
from bluebottle.activities.models import Activity, Contribution
from bluebottle.geo.models import Geolocation


class Event(Activity):
    capacity = models.PositiveIntegerField(null=True, blank=True)
    automatically_accept = models.BooleanField(default=True)

    location = models.ForeignKey(Geolocation, verbose_name=_('location'),
                                 null=True, blank=True, on_delete=models.SET_NULL)
    location_hint = models.TextField(_('location hint'), null=True, blank=True)

    start = models.DateTimeField(_('start'))
    end = models.DateTimeField(_('end'))
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

    def check_capacity(self):
        if len(self.participants) >= self.capacity and self.status == Event.Status.open:
            self.full()
            self.save()
        elif len(self.participants) < self.capacity and self.status == Event.Status.full:
            self.reopen()

    @property
    def duration(self):
        return (self.start - self.end).seconds / 60

    @property
    def participants(self):
        return self.contributions.filter(status=Participant.Status.new)

    def is_started(self):
        return self.start < now()

    def is_not_started(self):
        return self.start > now()

    def is_ended(self):
        return self.end < now()

    @Activity.status.transition(
        source=Activity.Status.draft,
        target=Activity.Status.open,
        serializer='bluebottle.events.serializers.EventSubmitSerializer',
    )
    def open(self, **kwargs):
        pass

    @Activity.status.transition(
        source=Activity.Status.open,
        target=Activity.Status.full,
        conditions=[is_not_started]
    )
    def full(self, **kwargs):
        pass

    @Activity.status.transition(
        source=Activity.Status.full,
        target=Activity.Status.open,
        conditions=[is_not_started]
    )
    def reopen(self, **kwargs):
        pass

    @Activity.status.transition(
        source=[Activity.Status.full, Activity.Status.open],
        target=Activity.Status.running,
        conditions=[is_started]
    )
    def do_start(self, **kwargs):
        pass

    @Activity.status.transition(
        source=Activity.Status.running,
        target=Activity.Status.done,
        conditions=[is_ended]
    )
    def done(self, **kwargs):
        for member in self.participants:
            member.success()
            member.save()

    @Activity.status.transition(
        source=[
            Activity.Status.open,
            Activity.Status.running,
            Activity.Status.done,
        ],
        target=Activity.Status.closed,
    )
    def close(self, **kwargs):
        pass

    @Activity.status.transition(
        source=Activity.Status.closed,
        target=Activity.Status.open,
        conditions=[is_not_started]
    )
    def extend(self, **kwargs):
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
        return self.activity.status == Activity.Status.open

    def event_is_open_or_full(self):
        return self.activity.status in (Activity.Status.open, Activity.Status.full)

    @property
    def owner(self):
        return self.user

    def save(self, *args, **kwargs):
        super(Participant, self).save(*args, **kwargs)

        if self.pk is None:
            follow(self.user, self.activity)

        self.activity.check_capacity()

    @Contribution.status.transition(
        source=Status.new,
        target=Status.withdrawn,
        conditions=[event_is_open_or_full]
    )
    def withdraw(self, **kwargs):
        unfollow(self.user, self.activity)

    @Contribution.status.transition(
        source=[Status.new],
        target=Status.rejected,
        permission=Contribution.is_activity_manager
    )
    def rejected(self, **kwargs):
        unfollow(self.user, self.activity)

    @Contribution.status.transition(
        source=[Status.new, Status.no_show, Status.rejected, Status.withdrawn],
        target=Status.success,
    )
    def success(self, **kwargs):
        follow(self.user, self.activity)
        self.time_spent = self.activity.duration

    @Contribution.status.transition(
        source=Status.success,
        target=Status.no_show,
        permission=Contribution.is_activity_manager
    )
    def no_show(self, **kwargs):
        unfollow(self.user, self.activity)
        self.time_spent = None

    @Contribution.status.transition(
        source='*',
        target=Status.closed,
    )
    def close(self, **kwargs):
        self.time_spent = None
