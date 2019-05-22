from django.db import models
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import ChoiceItem

from bluebottle.follow.models import follow, unfollow
from bluebottle.activities.models import Activity, Contribution
from bluebottle.notifications.decorators import transition


class Event(Activity):
    start = models.DateTimeField(_('start'))
    end = models.DateTimeField(_('end'))
    registration_deadline = models.DateTimeField(_('registration deadline'))
    capacity = models.PositiveIntegerField()
    automatically_accept = models.BooleanField(default=True)

    address = models.CharField(
        help_text=_('Address the event takes place'),
        max_length=200,
        null=True,
        blank=True
    )  # TODO:  Make this a foreign key to an address

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

    @property
    def duration(self):
        return (self.start - self.end).seconds / 60

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
        source=Activity.Status.open,
        target=Activity.Status.full,
    )
    def full(self, **kwargs):
        pass

    @transition(
        field='status',
        source=Activity.Status.full,
        target=Activity.Status.open,
    )
    def reopen(self, **kwargs):
        pass

    @transition(
        field='status',
        source=[Activity.Status.full, Activity.Status.open],
        target=Activity.Status.running,
    )
    def started(self, **kwargs):
        pass

    @transition(
        field='status',
        source=Activity.Status.running,
        target=Activity.Status.done,
    )
    def done(self, **kwargs):
        for member in self.participants:
            member.success()
            member.save()

    @transition(
        field='status',
        source=Activity.Status.open,
        target=Activity.Status.closed,
    )
    def closed(self, **kwargs):
        pass

    @transition(
        field='status',
        source=Activity.Status.closed,
        target=Activity.Status.open,
    )
    def extend(self, **kwargs):
        pass


class Participant(Contribution):
    class Status(Contribution.Status):
        going = ChoiceItem('going', _('going'))
        withdrawn = ChoiceItem('withdrawn', _('withdrawn'))
        rejected = ChoiceItem('rejected', _('rejected'))
        no_show = ChoiceItem('no_show', _('no_show'))
        closed = ChoiceItem('closed', _('closed'))

    time_spent = models.FloatField()

    def event_is_open(self):
        return self.activity.status == Activity.Status.open

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
