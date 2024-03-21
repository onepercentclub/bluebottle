import dateutil
from django.db.models import Count
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_json_api.relations import (
    ResourceRelatedField,
    HyperlinkedRelatedField,
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
)
from bluebottle.time_based.permissions import CanExportParticipantsPermission
from bluebottle.utils.serializers import ResourcePermissionField


class TimeBasedBaseSerializer(BaseActivitySerializer):
    title = serializers.CharField()
    description = serializers.CharField()
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
            'review_link',
            'review_title',
            'review_description',
            'review_document_enabled',
            'permissions',
            'registrations'
        )
        meta_fields = BaseActivitySerializer.Meta.meta_fields + ("registration_status",)

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'expertise',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
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

    def __init__(self, *args, **kwargs):
        self.statuses = kwargs.pop("statuses") or {}

        super().__init__(*args, **kwargs)

    def get_links(self, obj=None, lookup_field="pk"):
        return_data = super().get_links(obj, lookup_field)
        queryset = getattr(
            obj, self.source or self.field_name or self.parent.field_name
        )

        url = self.reverse(
            self.related_link_view_name, args=(getattr(obj, lookup_field),)
        )

        for name, statuses in self.statuses.items():
            return_data[name] = {
                "href": f'{url}?filter[status]={",".join(statuses)}',
                "meta": {"count": queryset.filter(status__in=statuses).count()},
            }

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
            "active": ["new", "succeeded"],
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
        TimeBasedBaseSerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class ScheduleActivitySerializer(TimeBasedBaseSerializer):
    detail_view_name = 'schedule-detail'
    export_view_name = 'schedule-participant-export'

    start = serializers.DateField(validators=[StartDateValidator()], allow_null=True)
    deadline = serializers.DateField(allow_null=True)
    is_online = serializers.BooleanField()

    contributors = RelatedLinkFieldByStatus(
        read_only=True,
        source="participants",
        related_link_view_name="schedule-participants",
        related_link_url_kwarg="activity_id",
        statuses={
            "unscheduled": ["accepted"],
            "failed": ["rejected", "withdrawn", "removed"],
            "active": ["scheduled", "succeeded"],
        },
    )
    registrations = RelatedLinkFieldByStatus(
        many=True,
        read_only=True,
        related_link_view_name="related-schedule-registrations",
        related_link_url_kwarg="activity_id",
        statuses={"new": ["new"], "accepted": ["accepted"], "rejected": ["rejected"]},
    )

    class Meta(TimeBasedBaseSerializer.Meta):
        model = ScheduleActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start',
            'deadline',
            'duration',
            'is_online',
            'location',
            'location_hint',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/schedules'
        included_resources = TimeBasedBaseSerializer.JSONAPIMeta.included_resources + [
            'location',
        ]

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
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
            "rejected": ["rejected", "stopped"],
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
        TimeBasedBaseSerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class DeadlineTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DeadlineActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'activities/time-based/deadline-transitions'
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
