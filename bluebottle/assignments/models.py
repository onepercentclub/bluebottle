from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.models import Activity, Contribution
from bluebottle.assignments.transitions import AssignmentTransitions, ApplicantTransitions
from bluebottle.fsm import TransitionManager


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

    transitions = TransitionManager(AssignmentTransitions, 'status')

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

    class JSONAPIMeta:
        resource_name = 'activities/assignments'

    def check_capcity(self):
        if len(self.accepted_applicants) >= self.capacity:
            self.transitions.full()
        else:
            self.transitions.reopen()


class Applicant(Contribution):
    motivation = models.TextField()

    time_spent = models.FloatField(_('time spent'))

    transitions = TransitionManager(ApplicantTransitions, 'status')
