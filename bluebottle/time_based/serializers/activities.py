from datetime import datetime, time

import dateutil
from django.db.models import Count
from django.db.models.functions import Trunc
from django.utils.timezone import now, get_current_timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_json_api.relations import (
    ResourceRelatedField,
    HyperlinkedRelatedField
)
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity, Organizer
from bluebottle.activities.utils import BaseActivitySerializer
from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.models import (
    DeadlineActivity,
    DeadlineParticipant,
    PeriodicActivity,
    ScheduleActivity,
    DateParticipant,
    DateActivity, RegisteredDateActivity, )
from bluebottle.time_based.permissions import CanExportParticipantsPermission
from bluebottle.utils.fields import RichTextField
from bluebottle.utils.serializers import ResourcePermissionField


class TimeBasedBaseSerializer(BaseActivitySerializer):
    review = serializers.BooleanField()
    registration_status = serializers.SerializerMethodField()

    def get_registration_status(self, instance):
        return dict(
            (item["status"], item["count"])
            for item in instance.registrations.values("status").annotate(
                count=Count("pk")
            )
        )

    def __init__(self, instance=None, *args, **kwargs):
        super().__init__(instance, *args, **kwargs)

        if not instance or instance.status in ('draft', 'needs_work'):
            for key in self.fields:
                self.fields[key].allow_blank = True
                self.fields[key].validators = []
                self.fields[key].allow_null = True
                self.fields[key].required = False

        self.fields['permissions'] = ResourcePermissionField(self.detail_view_name, view_args=('pk',))

        self.fields['participants_export_url'] = PrivateFileSerializer(
            self.export_view_name,
            url_args=('pk',),
            filename='participant.csv',
            permission=CanExportParticipantsPermission,
            read_only=True
        )

    class Meta(BaseActivitySerializer.Meta):
        fields = BaseActivitySerializer.Meta.fields + (
            'capacity',
            'registration_deadline',
            'expertise',
            'review',
            'registration_flow',
            'review_link',
            'review_title',
            'review_description',
            'review_document_enabled',
            'contributors',
            'registration_flow',
            'permissions',
            'registrations'
        )
        meta_fields = BaseActivitySerializer.Meta.meta_fields + ("registration_status",)

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'expertise',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers.serializers,
        **{
            'expertise': 'bluebottle.time_based.serializers.SkillSerializer',
        }
    )


class StartDateValidator():
    requires_context = True

    def __call__(self, value, serializer):
        parent = serializer.parent
        try:
            end = dateutil.parser.parse(parent.initial_data['deadline']).date()
        except (KeyError, TypeError):
            try:
                end = parent.instance.deadline
            except AttributeError:
                return

        if value and end and value > end:
            raise ValidationError('The activity should start before the deadline')


class PeriodActivitySerializer(ModelSerializer):
    activity_type = serializers.SerializerMethodField()

    def get_activity_type(self, instance):
        return instance.JSONAPIMeta.resource_name

    class Meta:
        model = Activity
        fields = (
            'activity_type',
            'slug'
        )
        resource_name = 'activities/time-based/periods'


class RelatedLinkFieldByStatus(HyperlinkedRelatedField):
    model = DeadlineParticipant

    def __init__(self, include_my=True, *args, **kwargs):
        self.statuses = kwargs.pop("statuses") or {}
        self.related_link_team_view_name = kwargs.pop(
            "related_link_team_view_name",
            None
        )
        self.include_my = include_my
        super().__init__(*args, **kwargs)

    def get_links(self, obj=None, lookup_field="pk"):
        return_data = super().get_links(obj, lookup_field)
        queryset = getattr(
            obj, self.source or self.field_name or self.parent.field_name
        )

        if self.related_link_team_view_name and getattr(obj, 'team_activity', None) == 'teams':
            url = self.reverse(
                self.related_link_team_view_name, args=(getattr(obj, lookup_field),)
            )
        else:
            url = self.reverse(
                self.related_link_view_name, args=(getattr(obj, lookup_field),)
            )

        for name, statuses in self.statuses.items():
            return_data[name] = {
                "href": f'{url}?filter[status]={",".join(statuses)}',
                "meta": {"count": queryset.filter(status__in=statuses).count()},
            }

        if self.include_my:
            if self.context['request'].user.is_authenticated:
                return_data['my'] = {
                    'href': url + '?filter[my]=true',
                    'meta': {
                        'count': queryset.filter(user=self.context['request'].user).count()
                    }
                }
            else:
                return_data['my'] = {
                    'href': url + '?filter[my]=true',
                    'meta': {
                        'count': 0
                    }

                }

        return_data['related'] = url

        return return_data


class DeadlineActivitySerializer(TimeBasedBaseSerializer):
    detail_view_name = 'deadline-detail'
    export_view_name = 'deadline-participant-export'

    start = serializers.DateField(validators=[StartDateValidator()], allow_null=True)
    deadline = serializers.DateField(allow_null=True)
    is_online = serializers.BooleanField()

    contributors = RelatedLinkFieldByStatus(
        read_only=True,
        source="participants",
        related_link_view_name="deadline-participants",
        related_link_url_kwarg="activity_id",
        statuses={
            "active": ["succeeded"],
            "failed": ["rejected", "withdrawn", "removed"],
        },
    )
    registrations = RelatedLinkFieldByStatus(
        many=True,
        read_only=True,
        related_link_view_name="related-deadline-registrations",
        related_link_url_kwarg="activity_id",
        statuses={"new": ["new"], "accepted": ["accepted"], "rejected": ["rejected"]},
    )

    class Meta(TimeBasedBaseSerializer.Meta):
        model = DeadlineActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start',
            'deadline',
            'duration',
            'is_online',
            'location',
            'location_hint',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/deadlines'
        included_resources = TimeBasedBaseSerializer.JSONAPIMeta.included_resources + [
            'location',
        ]

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers.serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class RegisteredDateActivitySerializer(TimeBasedBaseSerializer):
    detail_view_name = 'registered-date-detail'
    export_view_name = 'registered-date-participant-export'
    description = RichTextField(allow_blank=True)

    start = serializers.DateTimeField(allow_null=True)

    contributors = RelatedLinkFieldByStatus(
        read_only=True,
        source="participants",
        related_link_view_name="registered-date-participants",
        related_link_url_kwarg="activity_id",
        statuses={
            "active": ["succeeded", "accepted"],
            "failed": ["rejected", "withdrawn", "removed"],
        },
    )

    class Meta(TimeBasedBaseSerializer.Meta):
        model = RegisteredDateActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start',
            'end',
            'duration',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/registered-dates'

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers.serializers,
    )


class ScheduleActivitySerializer(TimeBasedBaseSerializer):
    detail_view_name = 'schedule-detail'

    start = serializers.DateField(validators=[StartDateValidator()], allow_null=True)
    deadline = serializers.DateField(allow_null=True)
    is_online = serializers.BooleanField()

    contributors = RelatedLinkFieldByStatus(
        read_only=True,
        source="participants",
        related_link_view_name="schedule-participants",
        related_link_team_view_name="team-schedule-participants",
        related_link_url_kwarg="activity_id",
        statuses={
            "unscheduled": ["accepted"],
            "active": ["scheduled", "succeeded"],
            "scheduled": ["scheduled"],
            "succeeded": ["succeeded"],
            "failed": ["rejected", "withdrawn", "removed", "cancelled"],
        },
    )

    teams = RelatedLinkFieldByStatus(
        read_only=True,
        related_link_view_name="related-teams",
        related_link_url_kwarg="activity_id",
        statuses={
            "unscheduled": ["accepted"],
            "active": ["scheduled", "succeeded"],
            "scheduled": ["scheduled"],
            "succeeded": ["succeeded"],
            "failed": ["rejected", "withdrawn", "removed", "cancelled"],
        },
    )

    registrations = RelatedLinkFieldByStatus(
        many=True,
        read_only=True,
        related_link_view_name="related-schedule-registrations",
        related_link_team_view_name="related-team-schedule-registrations",
        related_link_url_kwarg="activity_id",
        statuses={"new": ["new"], "accepted": ["accepted"], "rejected": ["rejected"]},
    )

    @property
    def export_view_name(self):
        if self.instance and self.instance.team_activity == "teams":
            return "team-schedule-participant-export"
        else:
            return "schedule-participant-export"

    class Meta(TimeBasedBaseSerializer.Meta):
        model = ScheduleActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            "start",
            "deadline",
            "duration",
            "is_online",
            "location",
            "location_hint",
            "team_activity",
            "teams",
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/schedules'
        included_resources = TimeBasedBaseSerializer.JSONAPIMeta.included_resources + [
            'location',
        ]

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers.serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class PeriodicActivitySerializer(TimeBasedBaseSerializer):
    detail_view_name = 'periodic-detail'
    export_view_name = 'periodic-participant-export'

    start = serializers.DateField(validators=[StartDateValidator()], allow_null=True)
    deadline = serializers.DateField(allow_null=True)
    is_online = serializers.BooleanField()

    contributors = RelatedLinkFieldByStatus(
        read_only=True,
        source="participants",
        related_link_view_name="periodic-participants",
        related_link_url_kwarg="activity_id",
        statuses={
            "active": ["new", "succeeded"],
            "failed": ["rejected", "withdrawn", "removed"],
        },
    )
    registrations = RelatedLinkFieldByStatus(
        read_only=True,
        related_link_view_name="related-periodic-registrations",
        related_link_url_kwarg="activity_id",
        statuses={
            "new": ["new"],
            "accepted": ["accepted"],
            "rejected": ["rejected", "stopped", "removed"],
        },
    )

    def get_contributor_count(self, instance):
        return (
            instance.deleted_successful_contributors
            + instance.contributors.not_instance_of(Organizer)
            .filter(status__in=["accepted", "participating"])
            .count()
        )

    class Meta(TimeBasedBaseSerializer.Meta):
        model = PeriodicActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start',
            'deadline',
            'duration',
            'period',
            'is_online',
            'location',
            'location_hint',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/periodics'
        included_resources = TimeBasedBaseSerializer.JSONAPIMeta.included_resources + [
            'location',
        ]

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers.serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class DateActivitySerializer(TimeBasedBaseSerializer):
    detail_view_name = 'date-detail'
    export_view_name = 'date-participant-export'

    date_info = serializers.SerializerMethodField()
    location_info = serializers.SerializerMethodField()

    contributors = RelatedLinkFieldByStatus(
        read_only=True,
        source="participants",
        related_link_view_name="date-participants",
        related_link_url_kwarg="activity_id",
        statuses={
            "active": ["new", "succeeded"],
            "failed": ["rejected", "withdrawn", "removed"],
        },
    )

    registrations = RelatedLinkFieldByStatus(
        read_only=True,
        related_link_view_name="related-date-registrations",
        related_link_url_kwarg="activity_id",
        statuses={
            "new": ["new"],
            "accepted": ["accepted"],
            "rejected": ["rejected", "removed", "withdrawn"]
        },
    )

    slots = RelatedLinkFieldByStatus(
        read_only=True,
        related_link_view_name="related-date-slots",
        related_link_url_kwarg="activity_id",
        include_my=False,
        statuses={
            "upcoming": ["open", "full", "running"],
            "passed": ["failed", "succeeded", "expired", "cancelled"],
            "total": ["open", "full", "running", "failed", "succeeded", "expired", "cancelled"],
        },
    )

    def get_contributor_count(self, instance):
        return (
            instance.deleted_successful_contributors
            + instance.contributors.not_instance_of(Organizer)
            .filter(status__in=["accepted", "participating"])
            .count()
        )

    def get_filtered_slots(self, obj, only_upcoming=False):

        start = self.context['request'].GET.get('filter[start]')
        end = self.context['request'].GET.get('filter[end]')
        tz = get_current_timezone()

        slots = obj.slots.exclude(status__in=['draft', 'cancelled']).all()
        try:
            if start:
                slots = slots.filter(start__gte=dateutil.parser.parse(start).astimezone(tz))
            elif only_upcoming:
                slots = slots.filter(start__gte=now())

            if end:
                slots = slots.filter(
                    start__lte=datetime.combine(dateutil.parser.parse(end), time.max).astimezone(tz)
                )
        except ValueError:
            pass

        return slots

    def get_date_info(self, obj):
        total = self.get_filtered_slots(obj).count()
        slots = self.get_filtered_slots(obj, only_upcoming=True)
        last_slot = obj.slots.exclude(status__in=['draft', 'cancelled']).order_by('start').last()
        end = last_slot.end if last_slot else None
        capacity = None
        duration = None

        if total > 1:
            starts = set(
                slots.annotate(date=Trunc('start', kind='day')).values_list('date')
            )
            count = len(slots)
            end = end.date()
            first = min(starts)[0].date() if starts else None
        elif total == 1:
            slot = self.get_filtered_slots(obj).first()
            first = slot.start
            duration = slot.duration
            count = 1
        else:
            first = None
            duration = None
            count = 0

        return {
            'total': total,
            'has_multiple': total > 1,
            'is_full': all(slot.status == 'full' for slot in slots),
            'count': count,
            'first': first,
            'end': end,
            'duration': duration,
            'capacity': capacity,
        }

    def get_location_info(self, obj):
        slots = self.get_filtered_slots(obj, only_upcoming=True)
        if not slots:
            slots = self.get_filtered_slots(obj, only_upcoming=False)
        is_online = len(slots) > 0 and len(slots.filter(is_online=True)) == len(slots)

        locations = slots.values_list(
            'location__locality',
            'location__country__alpha2_code',
            'location__formatted_address',
            'online_meeting_url',
            'location_hint'
        )

        if not len(slots) or not len(locations):
            return {
                'has_multiple': False,
                'is_online': is_online,
                'online_meeting_url': None,
                'location': None,
                'location_hint': None,
            }

        has_multiple = len(set(location[:2] for location in locations)) > 1 and not is_online
        if has_multiple:
            return {
                'has_multiple': True,
                'is_online': False,
                'online_meeting_url': None,
                'location': None,
                'location_hint': None,
            }
        slot = slots.first()

        if is_online or not slot.location:
            location = None
        else:
            location = {
                'locality': slot.location.locality if slot.location else None,
                'country': {
                    'code': slot.location.country.alpha2_code if slot.location.country else None,
                },
                'formattedAddress': slot.location.formatted_address if slot.location else None,
            }

        user = self.context['request'].user
        if (
                user.is_authenticated and
                obj.contributors.filter(user=user, status='accepted').instance_of(DateParticipant).count()
        ):
            meeting_url = slot.online_meeting_url or None
        else:
            meeting_url = None

        return {
            'has_multiple': False,
            'is_online': is_online,
            'online_meeting_url': meeting_url,
            'location': location,
            'location_hint': slot.location_hint,
        }

    class Meta(TimeBasedBaseSerializer.Meta):
        model = DateActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'slots',
            'date_info',
            'location_info',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/dates'


class DeadlineTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DeadlineActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'activities/time-based/deadline-transitions'
        included_resources = ['resource', ]


class RegisteredDateTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=RegisteredDateActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.RegisteredDateActivitySerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'activities/time-based/registered-date-transitions'
        included_resources = ['resource', ]


class ScheduleTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=ScheduleActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.ScheduleActivitySerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'activities/time-based/schedule-transitions'
        included_resources = ['resource', ]


class PeriodicTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=PeriodicActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.PeriodicActivitySerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'activities/time-based/periodic-transitions'
        included_resources = ['resource', ]


class DateTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DateActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DateActivitySerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'activities/time-based/date-transitions'
        included_resources = ['resource', ]
