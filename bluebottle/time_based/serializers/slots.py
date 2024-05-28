from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.fsm.serializers import AvailableTransitionsField, CurrentStatusField
from bluebottle.geo.models import Geolocation
from bluebottle.time_based.models import ScheduleSlot, TeamScheduleSlot
from bluebottle.time_based.serializers.activities import RelatedLinkFieldByStatus
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import ResourcePermissionField


class ScheduleSlotSerializer(ModelSerializer):
    is_online = serializers.BooleanField(required=False, allow_null=True)
    permissions = ResourcePermissionField("date-slot-detail", view_args=("pk",))
    transitions = AvailableTransitionsField(source="states")
    status = FSMField(read_only=True)
    location = ResourceRelatedField(
        queryset=Geolocation.objects, required=False, allow_null=True
    )
    current_status = CurrentStatusField(source="states.current_state")
    timezone = serializers.SerializerMethodField()

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
        )
        meta_fields = (
            "status",
            "current_status",
            "permissions",
            "transitions",
        )

    class JSONAPIMeta:
        resource_name = "activities/time-based/schedule-slots"
        included_resources = ["location", "activity"]

    included_serializers = {
        "location": "bluebottle.geo.serializers.GeolocationSerializer",
        "activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
    }


class TeamScheduleSlotSerializer(ScheduleSlotSerializer):
    participants = RelatedLinkFieldByStatus(
        read_only=True,
        related_link_view_name="slot-schedule-participants",
        related_link_url_kwarg="slot_id",
        statuses={
            "active": ["new", "succeeded"],
            "failed": ["rejected", "withdrawn", "removed"],
        },
    )

    class Meta(ScheduleSlotSerializer.Meta):
        model = TeamScheduleSlot
        fields = ScheduleSlotSerializer.Meta.fields + ("participants",)

    class JSONAPIMeta(ScheduleSlotSerializer.JSONAPIMeta):
        resource_name = "activities/time-based/team-schedule-slots"
