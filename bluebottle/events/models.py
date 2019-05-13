from django.db import models
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import ChoiceItem

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
    def accepted_members(self):
        return self.contributions.filter(status=Participant.Status.accepted)

    @property
    def attending_members(self):
        return self.contributions.filter(
            status__in=(Participant.Status.attending, Participant.Status.accepted)
        )

    @property
    def preview_data(self):
        return {
            'start': self.start,
            'end': self.end,
            'registration_deadline': self.registration_deadline,
            'capacity': self.capacity,
            'address': self.address,
            'attending': len(self.attending_members),
        }

    def check_capcity(self):
        if len(self.accepted_members) >= self.capacity and self.status == Activity.Status.open:
            self.full()
        elif self.status == Activity.Status.full:
            self.reopen()

    @transition(
        field='status',
        source=Activity.Status.open,
        target=Activity.Status.full,
        conditions=[Activity.initiative_is_approved]
    )
    def full(self):
        pass

    @transition(
        field='status',
        source=Activity.Status.full,
        target=Activity.Status.open,
        conditions=[Activity.initiative_is_approved]
    )
    def reopen(self):
        pass

    @transition(
        field='status',
        source=[Activity.Status.full, Activity.Status.open],
        target=Activity.Status.running,
        conditions=[Activity.initiative_is_approved]
    )
    def started(self):
        for member in self.accepted_members:
            member.attending()
            member.save()

    @transition(
        field='status',
        source=Activity.Status.running,
        target=Activity.Status.done,
        conditions=[Activity.initiative_is_approved]
    )
    def done(self):
        for member in self.attending_members:
            member.done()
            member.save()

    @transition(
        field='status',
        source=Activity.Status.open,
        target=Activity.Status.closed,
        conditions=[Activity.initiative_is_approved]
    )
    def closed(self):
        pass

    @transition(
        field='status',
        source=Activity.Status.closed,
        target=Activity.Status.open,
        conditions=[Activity.initiative_is_approved]
    )
    def extend(self):
        pass


class Participant(Contribution):
    class Status(Contribution.Status):
        accepted = ChoiceItem('accepted', _('accepted'))
        attending = ChoiceItem('attending', _('attending'))
        rejected = ChoiceItem('rejected', _('rejected'))
        absent = ChoiceItem('absent', _('absent'))
        withdrawn = ChoiceItem('withdrawn', _('withdrawn'))

    time_spent = models.FloatField()

    def event_is_open(self):
        return self.activity.status == Activity.Status.open

    def save(self, *args, **kwargs):
        if self.activity.automatically_accept:
            self.accept()

        super(Participant, self).save(*args, **kwargs)

    @transition(
        field='status',
        source=[Status.new, Status.rejected],
        target=Status.accepted,
        conditions=[event_is_open]
    )
    def accept(self):
        self.activity.check_capcity()

    @transition(
        field='status',
        source=[Status.new, Status.accepted],
        target=Status.rejected,
        conditions=[event_is_open]
    )
    def reject(self):
        self.activity.check_capcity()

    @transition(
        field='status',
        source=[Status.new, Status.accepted],
        target=Status.withdrawn,
        conditions=[event_is_open]
    )
    def withdrawn(self):
        self.activity.check_capcity()

    @transition(
        field='status',
        source=[Status.new, Status.accepted],
        target=Status.attending,
    )
    def attending(self):
        pass

    @transition(
        field='status',
        source=Status.attending,
        target=Status.success,
    )
    def success(self):
        self.time_spent = self.activity.duration

    @transition(
        field='status',
        source=[Status.success, Status.attending],
        target=Status.absent,
    )
    def absent(self):
        self.time_spent = None
