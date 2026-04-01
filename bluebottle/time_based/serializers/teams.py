from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework_json_api.relations import (
    ResourceRelatedField,
    HyperlinkedRelatedField,
)
from rest_framework_json_api.serializers import ModelSerializer, ValidationError

from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.fsm.serializers import (
    AvailableTransitionsField,
    CurrentStatusField,
    TransitionSerializer,
)
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.members.models import Member, MemberPlatformSettings
from bluebottle.time_based.models import Team, TeamMember, ScheduleActivity
from bluebottle.scim.models import SCIMPlatformSettings
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.serializers import ResourcePermissionField


class CountedHyperlinkedRelatedField(HyperlinkedRelatedField):

    def get_links(self, obj, id):
        links = super().get_links(obj, id)
        return {
            "related": links["related"],
            "members": {
                "href": links["related"],
                "meta": {"count": getattr(obj, self.parent.source).count()},
            }
        }


class CanExportTeamMembersPermission(IsOwner):
    """Allows access only to obj owner."""

    def has_object_action_permission(self, action, user, obj):
        return (
            obj.user == user
            or user in obj.activity.owners
            or user.is_staff
            or user.is_superuser
        ) and InitiativePlatformSettings.load().enable_participant_exports

    def has_action_permission(self, action, user, model_cls):
        return True


class TeamSerializer(ModelSerializer):
    permissions = ResourcePermissionField("team-detail", view_args=("pk",))
    registration = ResourceRelatedField(read_only=True)
    activity = ResourceRelatedField(queryset=ScheduleActivity.objects.all())
    user = ResourceRelatedField(read_only=True)
    slots = ResourceRelatedField(read_only=True, many=True)

    transitions = AvailableTransitionsField(source="states")
    current_status = CurrentStatusField(source="states.current_state")

    captain_email = serializers.SerializerMethodField()

    def get_captain_email(self, obj):
        user = self.context['request'].user
        if (
            user in obj.activity.owners or
            user.is_staff or
            user.is_superuser
        ):
            return obj.user.email
        return

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

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def to_representation(self, instance):
        result = super().to_representation(instance)

        user = self.context['request'].user
        if (user not in [
            instance.user,
            instance.activity.owner,
        ] and user not in instance.activity.owners and
            not user.is_staff and
            not user.is_superuser
        ):
            del result['invite_code']
        return result

    class Meta:
        model = Team
        fields = (
            "id",
            "registration",
            "invite_code",
            "activity",
            "user",
            "slots",
            "team_members",
            "member_export_url",
            "invite_code",
            "name",
            "description",
            "captain_email"
        )
        meta_fields = (
            "permissions",
            "transitions",
            "current_status",
        )

    class JSONAPIMeta:
        resource_name = "contributors/time-based/teams"
        included_resources = [
            "registration",
            "activity",
            "user",
            "slots",
            "slots.location",
            "slots.location.country",
        ]

    included_serializers = {
        "user": "bluebottle.initiatives.serializers.MemberSerializer",
        "activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
        "registration": "bluebottle.time_based.serializers.TeamScheduleRegistrationSerializer",
        "slots": "bluebottle.time_based.serializers.slots.TeamScheduleSlotSerializer",
        "slots.location": "bluebottle.geo.serializers.GeolocationSerializer",
        "slots.location.country": "bluebottle.geo.serializers.CountrySerializer",
    }


class TeamMemberSerializer(ModelSerializer):
    team = ResourceRelatedField(queryset=Team.objects)
    user = ResourceRelatedField(read_only=True)
    participants = ResourceRelatedField(read_only=True, many=True)

    permissions = ResourcePermissionField("team-member-detail", view_args=("pk",))
    transitions = AvailableTransitionsField(source="states")
    current_status = CurrentStatusField(source="states.current_state")
    invite_code = serializers.CharField(write_only=True, required=False)
    email = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = TeamMember
        fields = ("id", "team", "user", "invite_code", "participants", "email")
        meta_fields = ("permissions", "transitions", "current_status")

    class JSONAPIMeta:
        resource_name = "contributors/time-based/team-members"
        included_resources = ["team", "user", "team.activity", "participants"]

    included_serializers = {
        "team": "bluebottle.time_based.serializers.TeamSerializer",
        "team.activity": "bluebottle.time_based.serializers.activities.ScheduleActivitySerializer",
        "user": "bluebottle.initiatives.serializers.MemberSerializer",
        "participants": "bluebottle.time_based.serializers.TeamScheduleParticipantSerializer",
    }

    def create(self, validated_data):
        email = validated_data.pop("email", None)
        invite_code = validated_data.pop("invite_code", None)
        send_messages = validated_data.pop('send_messages', True)

        request = self.context.get("request")
        request_user = request.user if request else None

        if email:
            validated_data['user'] = Member.objects.filter(email__iexact=email).first()
            if not validated_data['user']:
                try:
                    validate_email(email)
                except Exception:
                    raise ValidationError(_('Not a valid email address'), code="invalid")

                member_settings = MemberPlatformSettings.load()
                scim_settings = SCIMPlatformSettings.load()

                if (
                    (member_settings.closed or member_settings.confirm_signup) and
                    not scim_settings.enabled
                ):
                    try:
                        validated_data['user'] = Member.create_by_email(email.strip())
                    except Exception:
                        raise ValidationError(_('Not a valid email address'), code="invalid")
                else:
                    raise ValidationError(_('User with email address not found'), code="not_found")
        else:
            if invite_code:
                validated_data["invite_code"] = invite_code
            if request_user and request_user.is_authenticated:
                validated_data["user"] = request_user

        if 'user' in validated_data and self.Meta.model.objects.filter(
            user=validated_data['user'], team=validated_data['team']
        ).exists():
            raise ValidationError('Already participating')

        validated_data['send_messages'] = send_messages
        return super().create(validated_data)


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


class TeamMemberTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=TeamMember.objects.all())
    field = "states"

    class JSONAPIMeta:
        resource_name = "contributors/time-based/team-member-transitions"
        fields = ("resource", "transition", )
        included_resources = [
            "resource",
            "resource.team",
            "resource.team.activity",
            "resource.participants"
        ]

    included_serializers = {
        "resource": "bluebottle.time_based.serializers.TeamMemberSerializer",
        "resource.team": "bluebottle.time_based.serializers.TeamSerializer",
        "resource.team.activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
        "resource.participants": "bluebottle.time_based.serializers.TeamScheduleParticipantSerializer",
    }
