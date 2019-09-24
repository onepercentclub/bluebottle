from django.db import models
from django.db.models import SET_NULL, Count, Sum
from django.utils.translation import ugettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem

from bluebottle.activities.models import Activity, Contribution
from bluebottle.assignments.transitions import AssignmentTransitions, ApplicantTransitions
from bluebottle.files.fields import DocumentField
from bluebottle.follow.models import follow
from bluebottle.fsm import TransitionManager
from bluebottle.geo.models import Geolocation


class Assignment(Activity):

    class EndDateTypes(DjangoChoices):
        deadline = ChoiceItem('deadline', label=_("Deadline"))
        on_date = ChoiceItem('on_date', label=_("On specific date"))

    registration_deadline = models.DateField(_('registration deadline'), null=True, blank=True)
    end_date = models.DateField(
        _('end date'), null=True, blank=True,
        help_text=_('Either the deadline or the date it will take place.'))
    duration = models.FloatField(_('duration'), null=True, blank=True)
    end_date_type = models.CharField(
        _('end date'), max_length=50, null=True, default=None, blank=True,
        help_text=_('Whether the end date is a deadline or a specific date the assignment takes place.'),
        choices=EndDateTypes.choices)

    capacity = models.PositiveIntegerField(_('capacity'), null=True, blank=True)
    expertise = models.ForeignKey('tasks.Skill', verbose_name=_('expertise'), blank=True, null=True)

    is_online = models.NullBooleanField(null=True, default=None)

    location = models.ForeignKey(
        Geolocation, verbose_name=_('assignment location'),
        null=True, blank=True, on_delete=SET_NULL)

    transitions = TransitionManager(AssignmentTransitions, 'status')
    complete_serializer = 'bluebottle.assignments.serializers.AssignmentValidationSerializer'

    @property
    def stats(self):
        stats = self.contributions.filter(
            status=ApplicantTransitions.values.succeeded).\
            aggregate(count=Count('user__id'), hours=Sum('applicant__time_spent'))
        committed = self.contributions.filter(
            status__in=[
                ApplicantTransitions.values.active,
                ApplicantTransitions.values.accepted]).\
            aggregate(committed_count=Count('user__id'), committed_hours=Sum('applicant__time_spent'))
        stats.update(committed)
        return stats

    class Meta:
        verbose_name = _("Assignment")
        verbose_name_plural = _("Assignments")
        ordering = ('-created',)
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

    @property
    def accepted_applicants(self):
        accepted_states = [
            ApplicantTransitions.values.accepted,
            ApplicantTransitions.values.active,
            ApplicantTransitions.values.succeeded
        ]
        return self.contributions.filter(status__in=accepted_states)

    def deadline_passed(self):
        if self.status in [AssignmentTransitions.values.running,
                           AssignmentTransitions.values.open]:
            if len(self.accepted_applicants):
                self.transitions.expire()
            else:
                self.transitions.succeed()


class Applicant(Contribution):
    motivation = models.TextField()
    time_spent = models.FloatField(_('time spent'), null=True, blank=True)
    transitions = TransitionManager(ApplicantTransitions, 'status')

    document = DocumentField(blank=True, null=True)

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

    def save(self, *args, **kwargs):
        created = self.pk is None
        super(Applicant, self).save(*args, **kwargs)
        if created:
            follow(self.user, self.activity)
            self.transitions.submit()
