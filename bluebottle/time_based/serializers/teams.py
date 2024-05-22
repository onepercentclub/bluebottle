from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import BaseContributorSerializer
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.models import Team, TeamMember
from bluebottle.utils.serializers import ResourcePermissionField


class TeamSerializer(BaseContributorSerializer):
    permissions = ResourcePermissionField("team-detail", view_args=("pk",))
    registration = ResourceRelatedField(read_only=True)
    activity = ResourceRelatedField(read_only=True)
    members = ResourceRelatedField(many=True, read_only=True)

    class Meta:
        model = Team
        fields = BaseContributorSerializer.Meta.fields + (
            "status",
            "registration",
            "members",
            "activity",
        )
        meta_fields = ("permissions",)

    class JSONAPIMeta:
        resource_name = "contributors/time-based/team"
        included_resources = ["members", "registration", "activity"]

    included_serializers = {
        "members": "bluebottle.time_based.serializers.TeamMemberSerializer",
        "activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
        "registration": "bluebottle.time_based.serializers.ScheduleRegistrationSerializer",
    }


class TeamMemberSerializer(BaseContributorSerializer):
    team = ResourceRelatedField(read_only=True)

    class Meta:
        model = TeamMember
        fields = BaseContributorSerializer.Meta.fields + ("status", "team")
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
