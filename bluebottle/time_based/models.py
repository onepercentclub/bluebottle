from django.db import models
from django.utils.translation import ugettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.activities.models import Activity, Contribution
from bluebottle.files.fields import PrivateDocumentField
from bluebottle.geo.models import Geolocation


class TimeBasedActivity(Activity):
    capacity = models.PositiveIntegerField(_('attendee limit'), null=True, blank=True)

    is_online = models.NullBooleanField(_('is online'), null=True, default=None)
    location = models.ForeignKey(Geolocation, verbose_name=_('location'),
                                 null=True, blank=True, on_delete=models.SET_NULL)
    location_hint = models.TextField(_('location hint'), null=True, blank=True)

    registration_deadline = models.DateField(_('deadline to apply'), null=True, blank=True)

    expertise = models.ForeignKey('tasks.Skill', verbose_name=_('skill'), blank=True, null=True)

    review = models.NullBooleanField(_('review applications'), null=True, default=None)

    @property
    def required_fields(self):
        fields = ['title', 'description', 'is_online', 'review', ]

        if not self.is_online:
            fields.append('location')

        return fields

    @property
    def accepted_applications(self):
        return self.contributions.instance_of(Application).filter(status='accepted')


class OnADateActivity(TimeBasedActivity):
    start = models.DateTimeField(_('activity date'), null=True, blank=True)

    duration = models.FloatField(_('duration'), null=True, blank=True)

    class Meta:
        verbose_name = _("On a date activity")
        verbose_name_plural = _("On A Date Activities")
        permissions = (
            ('api_read_onadateactivity', 'Can view on a date activities through the API'),
            ('api_add_onadateactivity', 'Can add on a date activities through the API'),
            ('api_change_onadateactivity', 'Can change on a date activities through the API'),
            ('api_delete_onadateactivity', 'Can delete on a date activities through the API'),

            ('api_read_own_onadateactivity', 'Can view own on a date activities through the API'),
            ('api_add_own_onadateactivity', 'Can add own on a date activities through the API'),
            ('api_change_own_onadateactivity', 'Can change own on a date activities through the API'),
            ('api_delete_own_onadateactivity', 'Can delete own on a date activities through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'activities/time-based/on-a-date'

    @property
    def required_fields(self):
        fields = super().required_fields

        return fields + ['start', 'duration']


class DurationPeriodChoices(DjangoChoices):
    overall = ChoiceItem('overall', label=_("overall"))
    day = ChoiceItem('day', label=_("per day"))
    week = ChoiceItem('week', label=_("per week"))
    month = ChoiceItem('month', label=_("per month"))


class WithADeadlineActivity(TimeBasedActivity):
    start = models.DateField(_('Start of activity'), null=True, blank=True)

    deadline = models.DateTimeField(_('deadline'), null=True, blank=True)

    duration = models.FloatField(_('duration'), null=True, blank=True)
    duration_period = models.CharField(
        _('duration period'),
        max_length=20,
        blank=True,
        null=True,
        choices=DurationPeriodChoices.choices,
    )

    class Meta:
        verbose_name = _("Activity with a deadline")
        verbose_name_plural = _("Activities with a deadline")
        permissions = (
            ('api_read_withadeadlineactivity', 'Can view activities with a deadline through the API'),
            ('api_add_withadeadlineactivity', 'Can add activities with a deadline through the API'),
            ('api_change_withadeadlineactivity', 'Can change activities with a deadline through the API'),
            ('api_delete_withadeadlineactivity', 'Can delete activities with a deadline through the API'),

            ('api_read_own_withadeadlineactivity', 'Can view own activities with a deadline through the API'),
            ('api_add_own_withadeadlineactivity', 'Can add own activities with a deadline through the API'),
            ('api_change_own_withadeadlineactivity', 'Can change own activities with a deadline through the API'),
            ('api_delete_own_withadeadlineactivity', 'Can delete own activities with a deadline through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'activities/time-based/with-a-deadline'

    @property
    def required_fields(self):
        fields = super().required_fields

        return fields + ['deadline', 'duration', 'duration_period']


class OngoingActivity(TimeBasedActivity):
    start = models.DateField(_('Start of activity'), null=True, blank=True)

    duration = models.FloatField(_('duration'), null=True, blank=True)
    duration_period = models.CharField(
        _('duration period'),
        max_length=20,
        blank=True,
        null=True,
        choices=DurationPeriodChoices.choices,
    )

    class Meta:
        verbose_name = _("Ongoing activity")
        verbose_name_plural = _("Ongoing activities")
        permissions = (
            ('api_read_ongoingactivity', 'Can view ongoing activities through the API'),
            ('api_add_ongoingactivity', 'Can add ongoing activities through the API'),
            ('api_change_ongoingactivity', 'Can change ongoing activities through the API'),
            ('api_delete_ongoingactivity', 'Can delete ongoing activities through the API'),

            ('api_read_own_ongoingactivity', 'Can view own ongoing activities through the API'),
            ('api_add_own_ongoingactivity', 'Can add own ongoing activities through the API'),
            ('api_change_own_ongoingactivity', 'Can change own ongoing activities through the API'),
            ('api_delete_own_ongoingactivity', 'Can delete own ongoing activities through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'activities/time-based/ongoing'

    @property
    def required_fields(self):
        fields = super().required_fields

        return fields + ['duration', 'duration_period']


class Application(Contribution):
    motivation = models.TextField(blank=True)
    document = PrivateDocumentField(blank=True, null=True)

    class Meta(object):
        verbose_name = _("Application")
        verbose_name_plural = _("Application")
        permissions = (
            ('api_read_application', 'Can view application through the API'),
            ('api_add_application', 'Can add application through the API'),
            ('api_change_application', 'Can change application through the API'),
            ('api_delete_application', 'Can delete application through the API'),

            ('api_read_own_application', 'Can view own application through the API'),
            ('api_add_own_application', 'Can add own application through the API'),
            ('api_change_own_application', 'Can change own application through the API'),
            ('api_delete_own_application', 'Can delete own application through the API'),
        )

    class JSONAPIMeta(object):
        resource_name = 'contributions/applications'

    def __str__(self):
        return self.user.full_name
