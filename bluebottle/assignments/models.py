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
from bluebottle.utils.models import Validator


class RegistrationDeadlineValidator(Validator):
    field = 'registration_deadline'
    code = 'registration_deadline'
    message = _('The registration deadline must be before the end'),

    def is_valid(self):
        return (
            not self.instance.registration_deadline or
            not self.instance.end_date or
            self.instance.registration_deadline < self.instance.end_date
        )


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

    validators = [RegistrationDeadlineValidator]

    @property
    def required_fields(self):
        fields = [
            'title', 'description', 'end_date_type', 'end_date',
            'registration_deadline', 'capacity', 'duration', 'is_online',
            'expertise'
        ]

        if not self.is_online:
            fields.append('location')

        return fields

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
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        ordering = ('-created',)
        permissions = (
            ('api_read_assignment', 'Can view task through the API'),
            ('api_add_assignment', 'Can add task through the API'),
            ('api_change_assignment', 'Can change task through the API'),
            ('api_delete_assignment', 'Can delete task through the API'),

            ('api_read_own_assignment', 'Can view own task through the API'),
            ('api_add_own_assignment', 'Can add own task through the API'),
            ('api_change_own_assignment', 'Can change own task through the API'),
            ('api_delete_own_assignment', 'Can delete own task through the API'),
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

    def registration_deadline_passed(self):
        # If registration deadline passed
        # got applicants -> start
        # no applicants -> expire
        if self.status in [AssignmentTransitions.values.full,
                           AssignmentTransitions.values.open]:
            if len(self.accepted_applicants):
                self.transitions.start()
            else:
                self.transitions.expire()

    def end_date_passed(self):
        # If end date passed
        # got applicants -> succeed
        # no applicants -> expire
        if self.status in [AssignmentTransitions.values.running,
                           AssignmentTransitions.values.full,
                           AssignmentTransitions.values.open]:
            if len(self.accepted_applicants):
                self.transitions.succeed()
            else:
                self.transitions.expire()

    def check_capacity(self):
        if self.capacity \
                and len(self.accepted_applicants) >= self.capacity \
                and self.status == AssignmentTransitions.values.open:
            self.transitions.lock()
            self.save()
        elif self.capacity \
                and len(self.accepted_applicants) < self.capacity \
                and self.status == AssignmentTransitions.values.full:
            self.transitions.reopen()
            self.save()


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
            self.transitions.initiate()
        self.activity.check_capacity()


from bluebottle.assignments.signals import *  # noqa
