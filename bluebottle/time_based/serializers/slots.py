from rest_framework import serializers
from rest_framework_json_api.serializers import ModelSerializer
from rest_framework_json_api.relations import ResourceRelatedField
from bluebottle.fsm.serializers import AvailableTransitionsField, CurrentStatusField
from bluebottle.geo.models import Geolocation
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.utils.fields import FSMField


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
        fields = (
            "id",
            "activity",
            "start",
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

    class JSONAPIMeta(object):
        included_resources = [
            "activity",
            "location",
        ]

    included_serializers = {
        "location": "bluebottle.geo.serializers.GeolocationSerializer",
        "activity": "bluebottle.time_based.serializers.ScheduleSerializer",
    }
