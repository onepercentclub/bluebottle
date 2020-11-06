from urllib.parse import urlencode

from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.utils.html import strip_tags
from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.activities.models import Activity, Contribution, ContributionValue
from bluebottle.files.fields import PrivateDocumentField
from bluebottle.geo.models import Geolocation

from html.parser import HTMLParser


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
    def applications(self):
        return self.contributions.instance_of(PeriodApplication, OnADateApplication)

    @property
    def active_applications(self):
        return self.applications.filter(status__in=('accepted', 'new',))

    @property
    def accepted_applications(self):
        return self.applications.filter(status='accepted')

    @property
    def durations(self):
        return Duration.objects.filter(
            contribution__activity=self
        )

    @property
    def accepted_durations(self):
        return self.durations.filter(
            contribution__status='accepted'
        )

    @property
    def values(self):
        return Duration.objects.filter(
            contribution__activity=self,
            status='succeeded'
        )


class OnADateActivity(TimeBasedActivity):
    start = models.DateTimeField(_('activity date'), null=True, blank=True)

    duration = models.DurationField(_('duration'), null=True, blank=True)

    duration_period = 'overall'

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

    @property
    def uid(self):
        return '{}-{}-{}'.format(connection.tenant.client_name, 'onadateactivity', self.pk)

    @property
    def google_calendar_link(self):
        def format_date(date):
            if date:
                return date.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

        url = u'https://calendar.google.com/calendar/render'
        params = {
            'action': u'TEMPLATE',
            'text': self.title,
            'dates': u'{}/{}'.format(
                format_date(self.start), format_date(self.start + self.duration)
            ),
            'details': HTMLParser().unescape(
                u'{}\n{}'.format(
                    strip_tags(self.description), self.get_absolute_url()
                )
            ),
            'uid': self.uid,
        }

        if self.location:
            params['location'] = self.location.formatted_address

        return u'{}?{}'.format(url, urlencode(params))

    @property
    def outlook_link(self):
        def format_date(date):
            if date:
                return date.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

        url = 'https://outlook.live.com/owa/'

        params = {
            'rru': 'addevent',
            'path': '/calendar/action/compose&rru=addevent',
            'allday': False,
            'subject': self.title,
            'startdt': format_date(self.start),
            'enddt': format_date(self.start + self.duration),
            'body': HTMLParser().unescape(
                u'{}\n{}'.format(
                    strip_tags(self.description), self.get_absolute_url()
                )
            ),
        }

        if self.location:
            params['location'] = self.location.formatted_address

        return u'{}?{}'.format(url, urlencode(params))


class DurationPeriodChoices(DjangoChoices):
    overall = ChoiceItem('overall', label=_("overall"))
    days = ChoiceItem('days', label=_("per day"))
    weeks = ChoiceItem('weeks', label=_("per week"))
    months = ChoiceItem('months', label=_("per month"))


class WithADeadlineActivity(TimeBasedActivity):
    start = models.DateField(_('start'), null=True, blank=True)

    deadline = models.DateField(_('deadline'), null=True, blank=True)

    duration = models.DurationField(_('duration'), null=True, blank=True)
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

    duration = models.DurationField(_('duration'), null=True, blank=True)
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


class Application():
    def __str__(self):
        return self.user.full_name

    @property
    def finished_durations(self):
        return self.contribution_values.filter(
            duration__end__lte=timezone.now()
        )


class OnADateApplication(Application, Contribution):
    motivation = models.TextField(blank=True)
    document = PrivateDocumentField(blank=True, null=True)

    class Meta(object):
        verbose_name = _("On a date application")
        verbose_name_plural = _("On a date application")
        permissions = (
            ('api_read_onadateapplication', 'Can view application through the API'),
            ('api_add_onadateapplication', 'Can add application through the API'),
            ('api_change_onadateapplication', 'Can change application through the API'),
            ('api_delete_onadateapplication', 'Can delete application through the API'),

            ('api_read_own_onadateapplication', 'Can view own application through the API'),
            ('api_add_own_onadateapplication', 'Can add own application through the API'),
            ('api_change_own_onadateapplication', 'Can change own application through the API'),
            ('api_delete_own_onadateapplication', 'Can delete own application through the API'),
        )


class PeriodApplication(Contribution, Application):
    motivation = models.TextField(blank=True)
    document = PrivateDocumentField(blank=True, null=True)

    current_period = models.DateField(null=True, blank=True)

    class Meta(object):
        verbose_name = _("Period application")
        verbose_name_plural = _("Period application")
        permissions = (
            ('api_read_periodapplication', 'Can view application through the API'),
            ('api_add_periodapplication', 'Can add application through the API'),
            ('api_change_periodapplication', 'Can change application through the API'),
            ('api_delete_periodapplication', 'Can delete application through the API'),

            ('api_read_own_periodapplication', 'Can view own application through the API'),
            ('api_add_own_periodapplication', 'Can add own application through the API'),
            ('api_change_own_periodapplication', 'Can change own application through the API'),
            ('api_delete_own_periodapplication', 'Can delete own application through the API'),
        )

    @property
    def current_duration(self):
        return self.contribution_values.get(status='new')


class Duration(ContributionValue):
    value = models.DurationField(_('value'))
    start = models.DateTimeField(_('start'))
    end = models.DateTimeField(_('end'), null=True, blank=True)


from bluebottle.time_based.periodic_tasks import *  # noqa
