from builtins import object
from collections.abc import Iterable

from django.conf import settings
from django.db.models import Count, Sum, Q
from django.utils.translation import gettext_lazy as _
from geopy.distance import distance, lonlat
from moneyed import Money
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework_json_api.relations import (
    ResourceRelatedField, SerializerMethodHyperlinkedRelatedField, SerializerMethodResourceRelatedField
)
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import (
    Activity, Contributor, Contribution, Organizer, EffortContribution, Team, Invite
)
from bluebottle.activities.permissions import CanExportTeamParticipantsPermission
from bluebottle.clients import properties
from bluebottle.collect.models import CollectContribution
from bluebottle.fsm.serializers import AvailableTransitionsField
from bluebottle.funding.models import MoneyContribution
from bluebottle.impact.models import ImpactGoal
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.members.models import Member
from bluebottle.time_based.models import TimeContribution, PeriodParticipant
from bluebottle.time_based.states import ParticipantStateMachine
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import FSMField, ValidationErrorsField, RequiredErrorsField
from bluebottle.utils.serializers import ResourcePermissionField, AnonymizedResourceRelatedField
from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer


class TeamSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    transitions = AvailableTransitionsField(source='states')

    members = SerializerMethodHyperlinkedRelatedField(
        model=Contributor,
        many=True,
        related_link_view_name='team-members',
        related_link_url_kwarg='team_id'
    )

    participants_export_url = PrivateFileSerializer(
        'team-members-export',
        url_args=('pk', ),
        filename='participants.csv',
        permission=CanExportTeamParticipantsPermission,
        read_only=True
    )

    def get_members(self, instance):
        user = self.context['request'].user
        return [
            contributor for contributor in instance.members.all() if (
                isinstance(contributor, PeriodParticipant) and (
                    contributor.status in [
                        ParticipantStateMachine.new.value,
                        ParticipantStateMachine.accepted.value,
                        ParticipantStateMachine.succeeded.value
                    ] or
                    user in (
                        instance.owner,
                        instance.activity.owner,
                        instance.activity.initiative.owner,
                        contributor.user
                    )
                )
            )
        ]

    class Meta(object):
        model = Team
        fields = ('owner', 'members', 'activity')
        meta_fields = (
            'status',
            'transitions',
            'created',
            'participants_export_url',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'owner',
        ]

        resource_name = 'activities/teams'

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class MatchingPropertiesField(serializers.ReadOnlyField):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        super().__init__(**kwargs)

    def to_representation(self, obj):
        user = self.context['request'].user
        matching = {'skill': None, 'theme': None, 'location': None}

        if user.is_authenticated:
            if obj.status != 'open':
                return {'skill': False, 'theme': False, 'location': False}

            if 'skills' not in self.context:
                self.context['skills'] = user.skills.all()

            if 'themes' not in self.context:
                self.context['themes'] = user.favourite_themes.all()

            if 'location' not in self.context:
                self.context['location'] = user.location or user.place

            if self.context['skills']:
                matching['skill'] = False
                try:
                    if obj.expertise in self.context['skills']:
                        matching['skill'] = True
                except AttributeError:
                    pass

            if self.context['themes']:
                matching['theme'] = False
                try:
                    if obj.initiative.theme in self.context['themes']:
                        matching['theme'] = True
                except AttributeError:
                    pass

            if self.context['location']:
                matching['location'] = False

                try:
                    if obj.is_online:
                        matching['location'] = True
                except AttributeError:
                    try:
                        if any(slot.is_online for slot in obj.slots.all()):
                            matching['location'] = True
                    except AttributeError:
                        pass

                positions = []
                try:
                    if obj.location and not obj.is_online:
                        positions = [obj.location.position.tuple]
                except AttributeError:
                    try:
                        positions = [
                            slot.location.position.tuple for slot in obj.slots.all()
                            if slot.location and not slot.is_online
                        ]
                    except AttributeError:
                        pass

                if positions and self.context['location'].position:
                    dist = min(
                        distance(
                            lonlat(*pos),
                            lonlat(*self.context['location'].position.tuple)
                        ) for pos in positions
                    )

                    if dist.km < settings.MATCHING_DISTANCE:
                        matching['location'] = True

        return matching


# This can't be in serializers because of circular imports
class BaseActivitySerializer(ModelSerializer):
    title = serializers.CharField(allow_blank=True, required=False)
    status = FSMField(read_only=True)
    owner = AnonymizedResourceRelatedField(read_only=True)
    permissions = ResourcePermissionField('activity-detail', view_args=('pk',))
    transitions = AvailableTransitionsField(source='states')
    contributor_count = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    is_follower = serializers.SerializerMethodField()
    type = serializers.CharField(read_only=True, source='JSONAPIMeta.resource_name')
    stats = serializers.OrderedDict(read_only=True)
    goals = ResourceRelatedField(required=False, many=True, queryset=ImpactGoal.objects.all())
    slug = serializers.CharField(read_only=True)

    matching_properties = MatchingPropertiesField()

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
        'goals.type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
        'image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'segments': 'bluebottle.segments.serializers.SegmentListSerializer',
        'segments.segment_type': 'bluebottle.segments.serializers.SegmentTypeSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'initiative.categories': 'bluebottle.categories.serializers.CategorySerializer',
        'initiative.theme': 'bluebottle.initiatives.serializers.ThemeSerializer',
        'initiative.location': 'bluebottle.geo.serializers.LocationSerializer',
        'initiative.activity_managers': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative.promoter': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    def get_is_follower(self, instance):
        user = self.context['request'].user
        return bool(user.is_authenticated) and instance.followers.filter(user=user).exists()

    def get_contributor_count(self, instance):
        return instance.contributors.not_instance_of(Organizer).filter(
            status__in=['accepted', 'succeeded', 'activity_refunded']
        ).count()

    def get_team_count(self, instance):
        return instance.teams.filter(status='open').count()

    class Meta(object):
        model = Activity
        fields = (
            'type',  # Needed for old style API endpoints like pages / page blocks
            'slug',
            'id',
            'image',
            'video_url',
            'initiative',
            'goals',
            'owner',
            'title',
            'description',
            'is_follower',
            'status',
            'stats',
            'errors',
            'required',
            'goals',
            'office_location',
            'segments',
            'team_activity'
        )

        meta_fields = (
            'permissions',
            'transitions',
            'created',
            'updated',
            'errors',
            'required',
            'matching_properties',
            'contributor_count',
            'team_count'
        )

    class JSONAPIMeta(object):
        included_resources = [
            'owner',
            'image',
            'initiative',
            'goals',
            'goals.type',
            'initiative.owner',
            'initiative.place',
            'initiative.location',
            'initiative.activity_managers',
            'initiative.promoter',
            'initiative.image',
            'initiative.categories',
            'initiative.theme',
            'segments',
            'segments.segment_type'
        ]
        resource_name = 'activities'


class BaseActivityListSerializer(ModelSerializer):
    title = serializers.CharField(allow_blank=True, required=False)
    status = FSMField(read_only=True)
    permissions = ResourcePermissionField('activity-detail', view_args=('pk',))
    owner = AnonymizedResourceRelatedField(read_only=True)
    is_follower = serializers.SerializerMethodField()
    type = serializers.CharField(read_only=True, source='JSONAPIMeta.resource_name')
    stats = serializers.OrderedDict(read_only=True)
    goals = ResourceRelatedField(required=False, many=True, queryset=ImpactGoal.objects.all())
    slug = serializers.CharField(read_only=True)
    matching_properties = MatchingPropertiesField()
    team_activity = SerializerMethodField()

    def get_team_activity(self, instance):
        if InitiativePlatformSettings.load().team_activities:
            return instance.team_activity
        return 'individuals'

    included_serializers = {
        'initiative': 'bluebottle.initiatives.serializers.InitiativeListSerializer',
        'initiative.location': 'bluebottle.geo.serializers.LocationSerializer',
        'image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
        'goals.type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
    }

    def get_is_follower(self, instance):
        user = self.context['request'].user
        return bool(user.is_authenticated) and instance.followers.filter(user=user).exists()

    class Meta(object):
        model = Activity
        fields = (
            'type',  # Needed for old style API endpoints like pages / page blocks
            'slug',
            'id',
            'image',
            'initiative',
            'owner',
            'title',
            'description',
            'is_follower',
            'status',
            'stats',
            'goals',
            'team_activity'
        )

        meta_fields = (
            'permissions',
            'created',
            'updated',
            'matching_properties',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'owner',
            'initiative',
            'image',
            'initiative.image',
            'initiative.location',
            'initiative.place',
            'goals',
            'goals.type',
        ]
        resource_name = 'activities'


class BaseTinyActivitySerializer(ModelSerializer):
    title = serializers.CharField(allow_blank=True, required=False)
    slug = serializers.CharField(read_only=True)

    class Meta(object):
        model = Activity
        fields = (
            'slug',
            'id',
            'title',
        )

        meta_fields = (
            'created',
            'updated',
        )

    class JSONAPIMeta(object):
        pass


class ActivitySubmitSerializer(ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(required=True, queryset=Member.objects.all())
    title = serializers.CharField(required=True)
    description = serializers.CharField(
        required=True,
        error_messages={
            'blank': _('Description is required'),
            'null': _('Description is required')
        }
    )

    class Meta(object):
        model = Activity
        fields = (
            'owner',
            'title',
            'description',
        )


# This can't be in serializers because of circular imports
class BaseContributorListSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    user = AnonymizedResourceRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.TinyActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(object):
        model = Contributor
        fields = ('user', 'activity', 'status', 'created', 'updated', 'accepted_invite', 'invite')
        meta_fields = ('created', 'updated', )

    class JSONAPIMeta(object):
        included_resources = [
            'user',
            'activity',
        ]
        resource_name = 'contributors'


# This can't be in serializers because of circular imports
class BaseContributorSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    user = AnonymizedResourceRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    team = ResourceRelatedField(read_only=True)
    transitions = AvailableTransitionsField(source='states')

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'invite': 'bluebottle.activities.utils.InviteSerializer',
        'team': 'bluebottle.activities.utils.TeamSerializer',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if (
            isinstance(self.instance, Iterable) or
            (
                self.instance and (
                    self.instance.accepted_invite or
                    self.instance.user != self.context['request'].user
                )
            )
        ):
            self.fields.pop('invite')

    class Meta(object):
        model = Contributor
        fields = ('user', 'activity', 'status', 'team', 'accepted_invite', 'invite',)
        meta_fields = ('transitions', 'created', 'updated', )

    class JSONAPIMeta(object):
        included_resources = [
            'user',
            'activity',
            'invite',
            'team'
        ]
        resource_name = 'contributors'


# This can't be in serializers because of circular imports
class BaseContributionSerializer(ModelSerializer):
    status = FSMField(read_only=True)

    class Meta(object):
        model = Contribution
        fields = ('value', 'status', )
        meta_fields = ('created', )

    class JSONAPIMeta(object):
        resource_name = 'contributors'


def get_stats_for_activities(activities):

    ids = activities.values_list('id', flat=True)

    default_currency = properties.DEFAULT_CURRENCY

    effort = EffortContribution.objects.filter(
        contribution_type='deed',
        status='succeeded',
        contributor__activity__id__in=ids
    ).aggregate(
        count=Count('id', distinct=True),
        activities=Count('contributor__activity', distinct=True)
    )

    time = TimeContribution.objects.filter(
        status='succeeded',
        contributor__activity__id__in=ids
    ).aggregate(
        count=Count('id', distinct=True),
        activities=Count('contributor__activity', distinct=True),
        value=Sum('value')
    )

    money = MoneyContribution.objects.filter(
        status='succeeded',
        contributor__activity__id__in=ids
    ).aggregate(
        count=Count('id', distinct=True),
        activities=Count('contributor__activity', distinct=True)
    )

    collect = CollectContribution.objects.filter(
        status='succeeded',
        contributor__user__isnull=False,
        contributor__activity__id__in=ids
    ).aggregate(
        count=Count('id', distinct=True),
        activities=Count('contributor__activity', distinct=True)
    )

    amounts = MoneyContribution.objects.filter(
        status='succeeded',
        contributor__activity__id__in=ids
    ).values(
        'value_currency'
    ).annotate(
        amount=Sum('value')
    ).order_by()

    contributor_count = Contributor.objects.filter(
        user__isnull=False,
        activity__id__in=ids,
        contributions__status='succeeded',
    ).exclude(
        Q(instance_of=Organizer)
    ).values('user_id').distinct().count()

    anonymous_donations = MoneyContribution.objects.filter(
        contributor__user__isnull=True,
        status='succeeded',
        contributor__activity__id__in=ids
    ).count()

    contributor_count += anonymous_donations

    collected = CollectContribution.objects.filter(
        status='succeeded',
        contributor__activity__id__in=ids
    ).values(
        'type_id'
    ).annotate(
        amount=Sum('value')
    ).order_by()

    amount = {
        'amount': sum(
            convert(
                Money(c['amount'], c['value_currency']),
                default_currency
            ).amount
            for c in amounts if c['amount']
        ),
        'currency': default_currency
    }

    return {
        'hours': time['value'].total_seconds() / 3600 if time['value'] else 0,
        'effort': effort['count'],
        'collected': dict((stat['type_id'], stat['amount']) for stat in collected),
        'activities': sum(stat['activities'] for stat in [effort, time, money, collect]),
        'contributors': contributor_count,
        'amount': amount
    }


class InviteSerializer(ModelSerializer):
    team = SerializerMethodResourceRelatedField(
        model=Team,
        many=False,
        read_only=True
    )

    def get_team(self, obj):
        return obj.contributor.team

    class Meta(object):
        model = Invite
        fields = ('id', 'team', )

    class JSONAPIMeta(object):
        included_resources = [
            'team', 'team.owner',
        ]

        resource_name = 'activities/invites'

    included_serializers = {
        'team': 'bluebottle.activities.utils.TeamSerializer',
        'team.owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }
