from rest_framework_json_api.relations import (
    ResourceRelatedField,
    HyperlinkedRelatedField,
)

from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.time_based.models import Team, TeamMember
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.fsm.serializers import (
    AvailableTransitionsField,
    CurrentStatusField,
    TransitionSerializer,
)

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.utils.permissions import IsOwner


class CountedHyperlinkedRelatedField(HyperlinkedRelatedField):

    def get_links(self, obj, id):
        links = super().get_links(obj, id)
        return {
            "related": {
                "href": links["related"],
                "meta": {"count": getattr(obj, self.parent.source).count()},
            }
        }


class CanExportTeamMembersPermission(IsOwner):
    """Allows access only to obj owner."""

    def has_object_action_permission(self, action, user, obj):
        return (
            obj.user == user
            or obj.activity.owner == user
            or user in obj.activity.initiative.activity_managers.all()
            or obj.activity.initiative.owner == user
            or user.is_staff
            or user.is_superuser
        ) and InitiativePlatformSettings.load().enable_participant_exports

    def has_action_permission(self, action, user, model_cls):
        return True


class TeamSerializer(ModelSerializer):
    permissions = ResourcePermissionField("team-detail", view_args=("pk",))
    registration = ResourceRelatedField(read_only=True)
    activity = ResourceRelatedField(read_only=True)
    team_members = ResourceRelatedField(many=True, read_only=True)
    user = ResourceRelatedField(read_only=True)

    transitions = AvailableTransitionsField(source="states")
    current_status = CurrentStatusField(source="states.current_state")

    team_members = CountedHyperlinkedRelatedField(
        read_only=True,
        many=True,
        related_link_view_name="related-team-members",
        related_link_url_kwarg="team_id",
    )
    member_export_url = PrivateFileSerializer(
        "team-members-export",
        url_args=("pk",),
        filename="team-members.csv",
        permission=CanExportTeamMembersPermission,
        read_only=True,
    )

    class Meta:
        model = Team
        fields = (
            "id",
            "status",
            "registration",
            "invite_code",
            "activity",
            "user",
            "slots",
            "team_members",
            "member_export_url",
        )
        meta_fields = (
            "permissions",
            "transitions",
            "current_status",
        )

    class JSONAPIMeta:
        resource_name = "contributors/time-based/teams"
        included_resources = ["registration", "activity", "captain", "slots"]

    included_serializers = {
        "user": "bluebottle.initiatives.serializers.MemberSerializer",
        "activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
        "registration": "bluebottle.time_based.serializers.ScheduleRegistrationSerializer",
        "slots": "bluebottle.time_based.serializers.TeamScheduleSlotSerializer",
    }


class TeamMemberSerializer(ModelSerializer):
    team = ResourceRelatedField(read_only=True)

    permissions = ResourcePermissionField("team-detail", view_args=("pk",))
    transitions = AvailableTransitionsField(source="states")
    current_status = CurrentStatusField(source="states.current_state")

    class Meta:
        model = TeamMember
        fields = ("id", "team", "transitions", "current_status", "user")
        meta_fields = ("permissions", "transitions", "current_status")

    class JSONAPIMeta:
        resource_name = "contributors/time-based/team-members"
        included_resources = ["team", "user"]

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
