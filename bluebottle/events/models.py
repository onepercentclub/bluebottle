from django.db import models
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import ChoiceItem

from bluebottle.events.messages import EventDoneOwnerMessage, EventClosedOwnerMessage
from bluebottle.follow.models import follow, unfollow
from bluebottle.activities.models import Activity, Contribution
from bluebottle.geo.models import Geolocation
from bluebottle.notifications.decorators import transition


from .tasks import *  # noqa


class Event(Activity):
    capacity = models.PositiveIntegerField(null=True, blank=True)
    automatically_accept = models.BooleanField(default=True)

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

    @property
    def duration(self):
        return (self.start_time - self.end_time).seconds / 60

    @property
    def participants(self):
        return self.contributions.filter(status=Participant.Status.going)

    def check_capcity(self):
        if len(self.participants) >= self.capacity and self.status == Activity.Status.open:
            self.full()
        elif self.status == Activity.Status.full:
            self.reopen()

    @transition(
        field='status',
        source=Activity.Status.draft,
        target=Activity.Status.open,
        form='bluebottle.events.forms.EventSubmitForm',
    )
    def submit(self, **kwargs):
        pass

    @transition(
        field='status',
        source=Activity.Status.open,
        target=Activity.Status.full,
    )
    def full(self, **kwargs):
        pass

    @transition(
        field='status',
        source=Activity.Status.full,
        target=Activity.Status.open,
        form='bluebottle.events.forms.EventSubmitForm',
    )
    def reopen(self, **kwargs):
        pass

    @transition(
        field='status',
        source=Activity.Status.closed,
        target=Activity.Status.draft,
    )
    def redraft(self, **kwargs):
        pass

    @transition(
        field='status',
        source=[Activity.Status.full, Activity.Status.open],
        target=Activity.Status.running,
    )
    def start(self, **kwargs):
        for member in self.participants:
            member.attending()
            member.save()

    @transition(
        field='status',
        source=Activity.Status.running,
        target=Activity.Status.done,
        messages=[EventDoneOwnerMessage]
    )
    def done(self, **kwargs):
        for member in self.participants:
            member.success()
            member.save()

    @transition(
        field='status',
        source=Activity.Status.open,
        target=Activity.Status.closed,
        messages=[EventClosedOwnerMessage]
    )
    def close(self, **kwargs):
        pass


class Participant(Contribution):
    class Status(Contribution.Status):
        going = ChoiceItem('going', _('going'))
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

    @property
    def owner(self):
        return self.user

    def save(self, *args, **kwargs):
        if self.status == self.Status.new:
            self.go()

        super(Participant, self).save(*args, **kwargs)

    @transition(
        field='status',
        source=(Status.new, Status.withdrawn, ),
        target=Status.going,
        conditions=[event_is_open]
    )
    def go(self, **kwargs):
        follow(self.user, self.activity)
        self.activity.check_capcity()

    @transition(
        field='status',
        source=Status.going,
        target=Status.withdrawn,
        conditions=[event_is_open]
    )
    def withdraw(self, **kwargs):
        unfollow(self.user, self.activity)
        self.activity.check_capcity()

    @transition(
        field='status',
        source=[Status.going],
        target=Status.rejected,
        permission=Contribution.is_activity_manager
    )
    def rejected(self, **kwargs):
        unfollow(self.user, self.activity)
        self.activity.check_capcity()

    @transition(
        field='status',
        source=[Status.going, Status.no_show, Status.rejected, Status.withdrawn],
        target=Status.success,
    )
    def success(self, **kwargs):
        follow(self.user, self.activity)
        self.time_spent = self.activity.duration

    @transition(
        field='status',
        source=Status.success,
        target=Status.no_show,
        permission=Contribution.is_activity_manager
    )
    def no_show(self, **kwargs):
        unfollow(self.user, self.activity)
        self.time_spent = None

    @transition(
        field='status',
        source='*',
        target=Status.closed,
    )
    def close(self, **kwargs):
        self.time_spent = None
