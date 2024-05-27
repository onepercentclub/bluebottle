from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.fsm.serializers import AvailableTransitionsField, CurrentStatusField
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.models import Team, TeamMember
from bluebottle.utils.serializers import ResourcePermissionField


class TeamSerializer(ModelSerializer):
    permissions = ResourcePermissionField("team-detail", view_args=("pk",))
    registration = ResourceRelatedField(read_only=True)
    activity = ResourceRelatedField(read_only=True)
    captain = ResourceRelatedField(read_only=True, source="user")

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
            "captain",
        )
        meta_fields = (
            "permissions",
            "transitions",
            "current_status",
        )

    class JSONAPIMeta:
        resource_name = "contributors/time-based/teams"
        included_resources = [
            "team_members",
            "registration",
            "activity",
            "captain",
            "slots"
        ]

    included_serializers = {
        "team_members": "bluebottle.time_based.serializers.TeamMemberSerializer",
        "slots": "bluebottle.time_based.serializers.slots.TeamScheduleSlot",
        "captain": "bluebottle.initiatives.serializers.MemberSerializer",
        "activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
        "registration": "bluebottle.time_based.serializers.ScheduleRegistrationSerializer",
    }


class TeamMemberSerializer(ModelSerializer):
    team = ResourceRelatedField(read_only=True)
    user = ResourceRelatedField(read_only=True)

    transitions = AvailableTransitionsField(source="states")
    current_status = CurrentStatusField(source="states.current_state")
    # permissions = ResourcePermissionField("team-member-detail", view_args=("pk",))

    class Meta:
        model = TeamMember
        fields = ("id", "team", "user")
        meta_fields = (
            # "permissions",
            "transitions",
            "current_status"
        )

    class JSONAPIMeta:
        resource_name = "contributors/time-based/team-members"
        included_resources = [
            "team",
            "user"
        ]

    included_serializers = {
        "team": "bluebottle.time_based.serializers.TeamSerializer",
        "user": "bluebottle.initiatives.serializers.MemberSerializer",
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
