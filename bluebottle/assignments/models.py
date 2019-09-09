from django.db import models
from django.db.models import SET_NULL
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.models import Activity, Contribution
from bluebottle.assignments.transitions import AssignmentTransitions, ApplicantTransitions
from bluebottle.fsm import TransitionManager
from bluebottle.geo.models import Geolocation


class Assignment(Activity):
    registration_deadline = models.DateField(_('registration deadline'), null=True, blank=True)
    deadline = models.DateField(_('deadline'), null=True, blank=True)
    duration = models.FloatField(_('duration'), null=True, blank=True)

    capacity = models.PositiveIntegerField(_('Capacity'), null=True, blank=True)
    expertise = models.ForeignKey('tasks.Skill', verbose_name=_('expertise'), blank=True, null=True)

    is_online = models.NullBooleanField(null=True, default=None)
    place = models.ForeignKey(
        Geolocation, verbose_name=_('Assignment location'),
        null=True, blank=True, on_delete=SET_NULL)

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

    class Meta:
        verbose_name = _("Applicant")
        verbose_name_plural = _("Applicants")
        permissions = (
            ('api_read_applicant', 'Can view applicant through the API'),
            ('api_add_applicant', 'Can add applicant through the API'),
            ('api_change_applicant', 'Can change applicant through the API'),
            ('api_delete_applicant', 'Can delete applicant through the API'),

            ('api_read_own_applicant', 'Can view own applicant through the API'),
            ('api_add_own_applicant', 'Can add own applicant through the API'),
            ('api_change_own_applicant', 'Can change own applicant through the API'),
            ('api_delete_own_applicant', 'Can delete own applicant through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'contributions/applicants'
