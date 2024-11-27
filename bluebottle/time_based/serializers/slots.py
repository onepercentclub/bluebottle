from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer, PolymorphicModelSerializer

from bluebottle.fsm.serializers import AvailableTransitionsField, CurrentStatusField
from bluebottle.geo.models import Geolocation
from bluebottle.time_based.models import ScheduleSlot, TeamScheduleSlot, PeriodicSlot, Slot
from bluebottle.time_based.serializers.activities import RelatedLinkFieldByStatus
from bluebottle.time_based.serializers.serializers import DateActivitySlotSerializer
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.utils.utils import reverse_signed


class ScheduleSlotSerializer(ModelSerializer):
    is_online = serializers.BooleanField(required=False, allow_null=True)
    permissions = ResourcePermissionField("schedule-slot-detail", view_args=("pk",))
    transitions = AvailableTransitionsField(source="states")
    status = FSMField(read_only=True)
    location = ResourceRelatedField(
        queryset=Geolocation.objects, required=False, allow_null=True
    )
    current_status = CurrentStatusField(source="states.current_state")
    timezone = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField()

    ical_view_name = "schedule-slot-ical"

    def get_links(self, instance):
        if instance.start and instance.duration:
            return {
                "ical": reverse_signed(self.ical_view_name, args=(instance.pk,)),
                "google": instance.google_calendar_link,
            }
        else:
            return {}

    def get_timezone(self, instance):
        return (
            instance.location.timezone
            if not instance.is_online and instance.location
            else None
        )

    class Meta:
        model = ScheduleSlot
        fields = (
            "id",
            "activity",
            "start",
            "duration",
            "end",
            "transitions",
            "is_online",
            "timezone",
            "location_hint",
            "online_meeting_url",
            "location",
            "links",
        )
        meta_fields = (
            "status",
            "current_status",
            "permissions",
            "transitions",
        )

    class JSONAPIMeta:
        resource_name = "activities/time-based/schedule-slots"
        included_resources = ["location", "location.country", "activity"]

    included_serializers = {
        "location": "bluebottle.geo.serializers.GeolocationSerializer",
        "location.country": "bluebottle.geo.serializers.CountrySerializer",
        "activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
    }


class TeamScheduleSlotSerializer(ScheduleSlotSerializer):
    permissions = ResourcePermissionField(
        "team-schedule-slot-detail", view_args=("pk",)
    )
    team = ResourceRelatedField(read_only=True)

    participants = RelatedLinkFieldByStatus(
        read_only=True,
        related_link_view_name="slot-schedule-participants",
        related_link_url_kwarg="slot_id",
        statuses={
            "active": ["new", "succeeded", "scheduled", "accepted"],
            "failed": ["rejected", "withdrawn", "removed", "cancelled"],
        },
    )
    ical_view_name = "team-schedule-slot-ical"

    class Meta(ScheduleSlotSerializer.Meta):
        model = TeamScheduleSlot
        fields = ScheduleSlotSerializer.Meta.fields + ("participants", "team")

    class JSONAPIMeta(ScheduleSlotSerializer.JSONAPIMeta):
        resource_name = "activities/time-based/team-schedule-slots"
        included_resources = ScheduleSlotSerializer.JSONAPIMeta.included_resources + ["team"]

    included_serializers = {
        "team": "bluebottle.time_based.serializers.teams.TeamSerializer",
        "location": "bluebottle.geo.serializers.GeolocationSerializer",
        "activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
    }


class PeriodicSlotSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    current_status = CurrentStatusField(source="states.current_state")

    class Meta:
        model = PeriodicSlot
        fields = (
            "id",
            "activity",
            "start",
            "duration",
            "end",
        )
        meta_fields = (
            "status",
            "current_status",
        )

    class JSONAPIMeta:
        resource_name = "activities/time-based/periodic-slots"
        included_resources = [
            "location",
            "location.country",
            "activity"
        ]

    included_serializers = {
        "location": "bluebottle.geo.serializers.GeolocationSerializer",
        "location.country": "bluebottle.geo.serializers.CountrySerializer",
        "activity": "bluebottle.time_based.serializers.PeriodicActivitySerializer",
    }


class SlotSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        PeriodicSlotSerializer,
        DateActivitySlotSerializer,
        ScheduleSlotSerializer,
        TeamScheduleSlotSerializer,
    ]

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = [
            'user',
            'activity',
        ]

    class Meta(object):
        model = Slot
        meta_fields = (
            'created',
            'updated',
            'current_status'
        )
