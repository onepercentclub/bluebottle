from future.utils import python_2_unicode_compatible

from builtins import object
from django.utils.timezone import datetime, timedelta, utc
from django.db import models
from django.db.models import SET_NULL, Count, Sum
from django.utils.translation import ugettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem

from timezonefinder import TimezoneFinder

import pytz

from bluebottle.activities.models import Activity, Contribution
from bluebottle.assignments.validators import RegistrationDeadlineValidator
from bluebottle.files.fields import PrivateDocumentField
from bluebottle.geo.models import Geolocation


tf = TimezoneFinder()


class Assignment(Activity):

    class EndDateTypes(DjangoChoices):
        deadline = ChoiceItem('deadline', label=_("Deadline"))
        on_date = ChoiceItem('on_date', label=_("On specific date"))

    registration_deadline = models.DateField(_('deadline to apply'), null=True, blank=True)
    start_time = models.TimeField(
        _('start time'), null=True, blank=True,
        help_text=_('On the specific task date, the start time.'))

    date = models.DateTimeField(
        _('date'), null=True, blank=True,
        help_text=_('Either the start date or the deadline of the task')
    )

    duration = models.FloatField(_('number of hours per person'), null=True, blank=True)
    preparation = models.FloatField(
        _('number of hours required for preparation'),
        null=True, blank=True,
        help_text=_('Only effective when task takes place on specific date.'))
    end_date_type = models.CharField(
        _('date type'), max_length=50, null=True, default=None, blank=True,
        help_text=_('Does the task have a deadline or does it take place on a specific date.'),
        choices=EndDateTypes.choices)

    capacity = models.PositiveIntegerField(_('number of people needed'), null=True, blank=True)
    expertise = models.ForeignKey('tasks.Skill', verbose_name=_('skill'), blank=True, null=True)

    is_online = models.NullBooleanField(null=True, default=None)

    location = models.ForeignKey(
        Geolocation, verbose_name=_('task location'),
        null=True, blank=True, on_delete=SET_NULL)

    validators = [RegistrationDeadlineValidator]

    @property
    def required_fields(self):
        fields = [
            'title', 'description', 'end_date_type', 'date',
            'capacity', 'duration', 'is_online',
            'expertise'
        ]

        if not self.is_online:
            fields.append('location')

        return fields

    @property
    def local_date(self):
        if self.location and self.location.position:
            tz_name = tf.timezone_at(
                lng=self.location.position.x,
                lat=self.location.position.y
            )
            tz = pytz.timezone(tz_name)

            return self.date.astimezone(tz).replace(tzinfo=None)
        else:
            return self.date

    @property
    def end(self):
        if self.duration and self.date:
            return self.date + timedelta(hours=self.duration)
        else:
            return self.date

    @property
    def start(self):
        if self.end_date_type == 'deadline' and self.registration_deadline:
            time = self.start_time or datetime.min.time()
            return datetime.combine(self.registration_deadline, time).replace(tzinfo=utc)
        return self.date

    @property
    def contribution_date(self):
        return self.date

    @property
    def stats(self):
        contributions = self.contributions.instance_of(Applicant)

        stats = contributions.filter(
            status='succeeded').\
            aggregate(count=Count('user__id'), hours=Sum('applicant__time_spent'))
        committed = contributions.filter(
            status__in=['active', 'accepted']).\
            aggregate(committed_count=Count('user__id'), committed_hours=Sum('applicant__time_spent'))
        stats.update(committed)
        return stats

    class Meta(object):
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

    class JSONAPIMeta(object):
        resource_name = 'activities/assignments'

    @property
    def accepted_applicants(self):
        accepted_states = ['accepted', 'active', 'succeeded']
        return self.contributions.instance_of(Applicant).filter(status__in=accepted_states)

    @property
    def new_applicants(self):
        return self.contributions.instance_of(Applicant).filter(status='new')

    @property
    def applicants(self):
        return self.contributions.instance_of(Applicant)

    @property
    def active_applicants(self):
        return self.contributions.instance_of(Applicant).filter(status__in=['active'])

    def save(self, *args, **kwargs):
        if self.preparation and self.end_date_type == "deadline":
            self.preparation = None
        return super(Assignment, self).save(*args, **kwargs)


@python_2_unicode_compatible
class Applicant(Contribution):
    motivation = models.TextField(blank=True)
    time_spent = models.FloatField(_('time spent'), null=True, blank=True)

    document = PrivateDocumentField(blank=True, null=True)

    class Meta(object):
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

    class JSONAPIMeta(object):
        resource_name = 'contributions/applicants'

    def delete(self, *args, **kwargs):
        super(Applicant, self).delete(*args, **kwargs)

    def __str__(self):
        return self.user.full_name


from bluebottle.assignments.states import *  # noqa
from bluebottle.assignments.triggers import *  # noqa
from bluebottle.assignments.periodic_tasks import *  # noqa
