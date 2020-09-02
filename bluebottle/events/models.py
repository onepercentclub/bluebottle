import datetime
from html.parser import HTMLParser

from django.db import models, connection
from django.db.models import Count, Sum
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import utc

from requests.models import PreparedRequest

from timezonefinder import TimezoneFinder

import pytz

from bluebottle.activities.models import Activity, Contribution
from bluebottle.events.validators import RegistrationDeadlineValidator
from bluebottle.geo.models import Geolocation


tf = TimezoneFinder()


class Event(Activity):
    capacity = models.PositiveIntegerField(_('attendee limit'), null=True, blank=True)
    automatically_accept = models.BooleanField(default=True)

    is_online = models.NullBooleanField(_('is online'), null=True, default=None)
    location = models.ForeignKey(Geolocation, verbose_name=_('location'),
                                 null=True, blank=True, on_delete=models.SET_NULL)
    location_hint = models.TextField(_('location hint'), null=True, blank=True)

    start_date = models.DateField(_('start date'), null=True, blank=True)
    start_time = models.TimeField(_('start time'), null=True, blank=True)
    start = models.DateTimeField(_('start date and time'), null=True, blank=True)
    duration = models.FloatField(_('duration'), null=True, blank=True)
    end = models.DateTimeField(_('end date and time'), null=True, blank=True)
    registration_deadline = models.DateField(_('deadline to apply'), null=True, blank=True)

    validators = [RegistrationDeadlineValidator]

    @property
    def required_fields(self):
        fields = ['title', 'description', 'start', 'duration', 'is_online', ]

        if not self.is_online:
            fields.append('location')

        return fields

    @property
    def stats(self):
        from .states import ParticipantStateMachine
        contributions = self.contributions.instance_of(Participant)

        stats = contributions.filter(
            status=ParticipantStateMachine.succeeded.value
        ).aggregate(
            count=Count('user__id'), hours=Sum('participant__time_spent')
        )
        committed = contributions.filter(
            status=ParticipantStateMachine.new.value
        ).aggregate(
            committed_count=Count('user__id'), committed_hours=Sum('participant__time_spent')
        )
        stats.update(committed)
        return stats

    @property
    def local_start(self):
        if self.location and self.location.position:
            tz_name = tf.timezone_at(
                lng=self.location.position.x,
                lat=self.location.position.y
            )
            tz = pytz.timezone(tz_name)
            return self.start.astimezone(tz).replace(tzinfo=None)
        else:
            return self.start

    @property
    def contribution_date(self):
        return self.start

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

    class JSONAPIMeta:
        resource_name = 'activities/events'

    @property
    def current_end(self):
        if self.start and self.duration:
            return self.start + datetime.timedelta(hours=self.duration)

    def save(self, *args, **kwargs):
        self.end = self.current_end

        super(Event, self).save(*args, **kwargs)

    @property
    def participants(self):
        from .states import ParticipantStateMachine
        return self.contributions.filter(
            status__in=[
                ParticipantStateMachine.new.value,
                ParticipantStateMachine.succeeded.value
            ]
        ).instance_of(Participant)

    @property
    def uid(self):
        return '{}-{}-{}'.format(connection.tenant.client_name, 'event', self.pk)

    @property
    def google_calendar_link(self):
        def format_date(date):
            if date:
                return date.astimezone(utc).strftime('%Y%m%dT%H%M%SZ')

        prepared_request = PreparedRequest()

        url = 'https://calendar.google.com/calendar/render'
        params = {
            'action': 'TEMPLATE',
            'text': self.title,
            'dates': '{}/{}'.format(
                format_date(self.start), format_date(self.end)
            ),
            'details': HTMLParser().unescape(
                '{}\n{}'.format(
                    strip_tags(self.description), self.get_absolute_url()
                )
            ),
            'uid': self.uid,
        }

        if self.location:
            params['location'] = self.location.formatted_address

        prepared_request.prepare_url(url, params)
        return prepared_request.url

    @property
    def outlook_link(self):
        def format_date(date):
            if date:
                return date.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S')

        prepared_request = PreparedRequest()
        url = 'https://outlook.live.com/owa/'

        params = {
            'rru': 'addevent',
            'path': '/calendar/action/compose&rru=addevent',
            'allday': False,
            'subject': self.title,
            'startdt': format_date(self.start),
            'enddt': format_date(self.end),
            'body': HTMLParser().unescape(
                '{}\n{}'.format(
                    strip_tags(self.description), self.get_absolute_url()
                )
            ),
        }

        if self.location:
            params['location'] = self.location.formatted_address

        prepared_request.prepare_url(url, params)
        return prepared_request.url


class Participant(Contribution):
    time_spent = models.FloatField(default=0)

    class Meta:
        verbose_name = _("Participant")
        verbose_name_plural = _("Participants")

        permissions = (
            ('api_read_participant', 'Can view participant through the API'),
            ('api_add_participant', 'Can add participant through the API'),
            ('api_change_participant', 'Can change participant through the API'),
            ('api_delete_participant', 'Can delete participant through the API'),

            ('api_read_own_participant', 'Can view own participant through the API'),
            ('api_add_own_participant', 'Can add own participant through the API'),
            ('api_change_own_participant', 'Can change own participant through the API'),
            ('api_delete_own_participant', 'Can delete own participant through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'contributions/participants'

    def save(self, *args, **kwargs):
        if not self.contribution_date:
            self.contribution_date = self.activity.start

        super(Participant, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.user.full_name


from bluebottle.events.states import *  # noqa
from bluebottle.events.triggers import *  # noqa
from bluebottle.events.periodic_tasks import *  # noqa
