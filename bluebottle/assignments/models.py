from django.db import models
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import ChoiceItem

from bluebottle.activities.models import Activity, Contribution
from bluebottle.notifications.decorators import transition


class Assignment(Activity):
    registration_deadline = models.DateTimeField(_('registration deadline'))
    end_time = models.DateField(_('End time'))
    capacity = models.PositiveIntegerField()

    expertise = models.ForeignKey('tasks.Skill', verbose_name=_('expertise'), null=True)

    location = models.CharField(
        help_text=_('Location the assignment takes place'),
        max_length=200,
        null=True,
        blank=True
    )  # TODO:  Make this a foreign key to an address

    class Meta:
        verbose_name = _("Assignment")
        verbose_name_plural = _("Assignments")
        permissions = (
            ('api_read_assignment', 'Can view assignment through the API'),
            ('api_add_assignment', 'Can add assignment through the API'),
            ('api_change_assignment', 'Can change assignment through the API'),
            ('api_delete_assignment', 'Can delete assignment through the API'),

            ('api_read_own_assignment', 'Can view own assignment through the API'),
            ('api_add_own_assignment', 'Can add own assignment through the API'),
            ('api_change_own_assignment', 'Can change own assignment through the API'),
            ('api_delete_own_assignment', 'Can delete own assignment through the API'),
        )

    def check_capcity(self):
        if len(self.accepted_applicants) >= self.capacity:
            self.full()
        else:
            self.reopen()

    @transition(
        field='status',
        source=Activity.Status.open,
        target=Activity.Status.running,
    )
    def start(self, **kwargs):
        pass

    @transition(
        field='status',
        source=Activity.Status.running,
        target=Activity.Status.done,
    )
    def success(self, **kwargs):
        for member in self.accepted_applicants:
            member.success()
            member.save()

    @transition(
        field='status',
        source=Activity.Status.running,
        target=Activity.Status.closed,
    )
    def close(self, **kwargs):
        for member in self.accepted_applicants:
            member.fail()
            member.save()

    @transition(
        field='status',
        source=[Activity.Status.closed, Activity.Status.done, Activity.Status.running],
        target=Activity.Status.open,
    )
    def extend_deadline(self, **kwargs):
        pass

    @transition(
        field='status',
        source=[Activity.Status.closed, Activity.Status.done],
        target=Activity.Status.running,
    )
    def extend(self, **kwargs):
        pass


class Applicant(Contribution):
    class Status(Contribution.Status):
        accepted = ChoiceItem('accepted', _('accepted'))
        rejected = ChoiceItem('rejected', _('rejected'))
        withdrawn = ChoiceItem('withdrawn', _('withdrawn'))
        active = ChoiceItem('attending', _('done'))

    motivation = models.TextField()

    time_spent = models.FloatField(_('time spent'))

    @property
    def assignment_is_open(self):
        return self.event_.status == Activity.Status.open

    @transition(
        field='status',
        source=[Status.new, Status.rejected],
        target=Status.accepted,
        conditions=[assignment_is_open]
    )
    def accept(self):
        self.event_.check_capcity()

    @transition(
        field='status',
        source=[Status.new, Status.accepted],
        target=Status.rejected,
        conditions=[assignment_is_open]
    )
    def reject(self):
        self.event_.check_capcity()

    @transition(
        field='status',
        source=[Status.new, Status.accepted],
        target=Status.withdrawn,
        conditions=[assignment_is_open]
    )
    def withdraw(self):
        self.event_.check_capcity()

    @transition(
        field='status',
        source=Status.accepted,
        target=Status.active,
    )
    def activate(self):
        pass

    @transition(
        field='status',
        source=[Status.active, Status.failed],
        target=Status.success,
    )
    def success(self):
        pass

    @transition(
        field='status',
        source=[Status.success, Status.active],
        target=Status.failed,
    )
    def fail(self):
        self.time_spent = None
