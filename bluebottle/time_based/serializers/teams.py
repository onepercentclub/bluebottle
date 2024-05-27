from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from rest_framework_json_api.serializers import ModelSerializer
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.models import Team, TeamMember
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.utils.fields import FSMField
from bluebottle.fsm.serializers import AvailableTransitionsField, CurrentStatusField


class TeamSerializer(ModelSerializer):
    permissions = ResourcePermissionField("team-detail", view_args=("pk",))
    registration = ResourceRelatedField(read_only=True)
    activity = ResourceRelatedField(read_only=True)
    team_members = ResourceRelatedField(many=True, read_only=True)
    user = ResourceRelatedField(read_only=True)

    transitions = AvailableTransitionsField(source="states")
    current_status = CurrentStatusField(source="states.current_state")

    class Meta:
        model = Team
        fields = (
            "id",
            "status",
            "registration",
            "team_members",
            "activity",
            "user",
            "slots",
        )
        meta_fields = (
            "permissions",
            "transitions",
            "current_status",
        )

    class JSONAPIMeta:
        resource_name = "contributors/time-based/teams"
        included_resources = ["members", "registration", "activity", "captain"]

    included_serializers = {
        "members": "bluebottle.time_based.serializers.TeamMemberSerializer",
        "user": "bluebottle.initiatives.serializers.MemberSerializer",
        "activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
        "registration": "bluebottle.time_based.serializers.ScheduleRegistrationSerializer",
    }


class TeamMemberSerializer(ModelSerializer):
    team = ResourceRelatedField(read_only=True)

    transitions = AvailableTransitionsField(source="states")
    current_status = CurrentStatusField(source="states.current_state")

    class Meta:
        model = TeamMember
        fields = ("id", "status", "team" "transitions", "current_status")
        meta_fields = ("permissions",)

    class JSONAPIMeta:
        resource_name = "contributors/time-based/team-member"
        included_resources = [
            "team",
        ]

    included_serializers = {
        "team": "bluebottle.time_based.serializers.TeamSerializer",
    }


class TeamTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Team.objects.all())
    field = "states"

    class JSONAPIMeta:
        resource_name = "contributors/time-based/team-transitions"
        included_resources = ["resource", "resource.activity"]

    included_serializers = {
        "resource": "bluebottle.time_based.serializers.TeamSerializer",
        "resource.activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
    }
