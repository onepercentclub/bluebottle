from django.db import models
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import ChoiceItem

from bluebottle.activities.models import Activity, Contribution
from bluebottle.notifications.decorators import transition


class Job(Activity):
    registration_deadline = models.DateTimeField(_('registration deadline'))
    end = models.DateField(_('end'))
    capacity = models.PositiveIntegerField()

    expertise = models.ForeignKey('tasks.Skill', verbose_name=_('expertise'), null=True)

    location = models.CharField(
        help_text=_('Location the job takes place'),
        max_length=200,
        null=True,
        blank=True
    )  # TODO:  Make this a foreign key to an address

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")
        permissions = (
            ('api_read_job', 'Can view job through the API'),
            ('api_add_job', 'Can add job through the API'),
            ('api_change_job', 'Can change job through the API'),
            ('api_delete_job', 'Can delete job through the API'),

            ('api_read_own_job', 'Can view own job through the API'),
            ('api_add_own_job', 'Can add own job through the API'),
            ('api_change_own_job', 'Can change own job through the API'),
            ('api_delete_own_job', 'Can delete own job through the API'),
        )

    @property
    def preview_data(self):
        return {
            'registration_deadline': self.registration_deadline,
            'end': self.end,
            'capacity': self.capacity,
            'location': self.address,
            'applicants': len(self.applicants),
            'expertise': self.expertise,
        }

    def check_capcity(self):
        if len(self.accepted_applicants) >= self.capacity:
            self.full()
        else:
            self.reopen()

    @transition(
        field='status',
        source=Activity.Status.open,
        target=Activity.Status.running,
        conditions=[Activity.initiative_is_approved]
    )
    def start(self):
        pass

    @transition(
        field='status',
        source=Activity.Status.running,
        target=Activity.Status.done,
        conditions=[Activity.initiative_is_approved]
    )
    def success(self):
        for member in self.accepted_applicants:
            member.success()
            member.save()

    @transition(
        field='status',
        source=Activity.Status.running,
        target=Activity.Status.closed,
        conditions=[Activity.initiative_is_approved]
    )
    def close(self):
        for member in self.accepted_applicants:
            member.fail()
            member.save()

    @transition(
        field='status',
        source=[Activity.Status.closed, Activity.Status.done, Activity.Status.running],
        target=Activity.Status.open,
        conditions=[Activity.initiative_is_approved]
    )
    def extend_deadline(self):
        pass

    @transition(
        field='status',
        source=[Activity.Status.closed, Activity.Status.done],
        target=Activity.Status.running,
        conditions=[Activity.initiative_is_approved]
    )
    def extend(self):
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
    def job_is_open(self):
        return self.event_.status == Activity.Status.open

    @transition(
        field='status',
        source=[Status.new, Status.rejected],
        target=Status.accepted,
        conditions=[job_is_open]
    )
    def accept(self):
        self.event_.check_capcity()

    @transition(
        field='status',
        source=[Status.new, Status.accepted],
        target=Status.rejected,
        conditions=[job_is_open]
    )
    def reject(self):
        self.event_.check_capcity()

    @transition(
        field='status',
        source=[Status.new, Status.accepted],
        target=Status.withdrawn,
        conditions=[job_is_open]
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
