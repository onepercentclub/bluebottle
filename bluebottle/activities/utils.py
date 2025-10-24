from builtins import object
from gc import get_objects
from itertools import groupby

from django.conf import settings
from django.db.models import Count, Sum, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_tools.middlewares.ThreadLocal import get_current_user
from geopy.distance import distance, lonlat
from moneyed import Money
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework_json_api.relations import (
    ResourceRelatedField, SerializerMethodResourceRelatedField,
    HyperlinkedRelatedField,
    PolymorphicResourceRelatedField,
)
from rest_framework_json_api.serializers import ModelSerializer, PolymorphicModelSerializer

from bluebottle.activities.models import (
    Activity, Contributor, Contribution, Organizer, EffortContribution, Team, Invite,
    ActivityAnswer, TextAnswer, SegmentAnswer, FileUploadAnswer,
    ConfirmationAnswer
)
from bluebottle.clients import properties
from bluebottle.collect.models import CollectType, CollectActivity, CollectContributor
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.files.serializers import DocumentSerializer
from bluebottle.fsm.serializers import AvailableTransitionsField, CurrentStatusField
from bluebottle.funding.models import MoneyContribution
from bluebottle.impact.models import ImpactGoal
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.members.models import Member, MemberPlatformSettings
from bluebottle.organizations.models import Organization
from bluebottle.segments.models import Segment
from bluebottle.time_based.models import (
    TimeContribution, DeadlineActivity, DeadlineParticipant,
    DateActivitySlot, DateParticipant, RegisteredDateParticipant, RegisteredDateActivity
)
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import FSMField, RichTextField, ValidationErrorsField, RequiredErrorsField, \
    PolymorphicManySerializerMethodResourceRelatedField, PolymorphicSerializerMethodResourceRelatedField
from bluebottle.utils.serializers import ResourcePermissionField


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


class BaseAnswerSerializer(ModelSerializer):
    class Meta:
        fields = ('activity', 'question')

    class JSONAPIMeta:
        included_resources = ['activity', 'question']

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivitySerializer',
        'question': 'bluebottle.activities.serializers.ActivityQuestionSerializer',
    }


class TextAnswerSerializer(BaseAnswerSerializer):
    class Meta(BaseAnswerSerializer.Meta):
        model = TextAnswer
        fields = BaseAnswerSerializer.Meta.fields + ('answer', )

    class JSONAPIMeta(BaseAnswerSerializer.JSONAPIMeta):
        resource_name = 'text-answers'


class ConfirmationAnswerSerializer(BaseAnswerSerializer):
    class Meta(BaseAnswerSerializer.Meta):
        model = ConfirmationAnswer
        fields = BaseAnswerSerializer.Meta.fields + ('confirmed', )

    class JSONAPIMeta(BaseAnswerSerializer.JSONAPIMeta):
        resource_name = 'confirmation-answers'


class SegmentAnswerSerializer(BaseAnswerSerializer):
    class Meta(BaseAnswerSerializer.Meta):
        model = SegmentAnswer
        fields = BaseAnswerSerializer.Meta.fields + ('segment', )

    class JSONAPIMeta(BaseAnswerSerializer.JSONAPIMeta):
        resource_name = 'segment-answers'
        included_resources = BaseAnswerSerializer.JSONAPIMeta.included_resources + ['segment']

    included_serializers = {
        'segment': 'bluebottle.segments.serializers.SegmentDetailSerializer',
        'activity': 'bluebottle.activities.serializers.ActivitySerializer',
        'question': 'bluebottle.activities.serializers.ActivityQuestionSerializer',
    }


class FileUploadAnswerDocumentSerializer(DocumentSerializer):
    content_view_name = 'file-upload-answer-document'
    relationship = 'fileuploadanswer_set'


class FileUploadAnswerSerializer(BaseAnswerSerializer):
    class Meta(BaseAnswerSerializer.Meta):
        model = FileUploadAnswer
        fields = BaseAnswerSerializer.Meta.fields + ('file', )

    class JSONAPIMeta(BaseAnswerSerializer.JSONAPIMeta):
        resource_name = 'file-upload-answers'
        included_resources = ['file']

    included_serializers = {
        'file': 'bluebottle.activities.serializers.FileUploadAnswerDocumentSerializer'
    }


class ActivityAnswerSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        TextAnswerSerializer,
        ConfirmationAnswerSerializer,
        SegmentAnswerSerializer,
        FileUploadAnswerSerializer
    ]

    class Meta():
        model = ActivityAnswer

    class JSONAPIMeta:
        included_resources = ['question', 'segment', 'file']

    included_serializers = {
        'question': 'bluebottle.activities.serializers.ActivityQuestionSerializer',
        'segment': 'bluebottle.segments.serializers.SegmentListSerializer',
        'file': 'bluebottle.activities.serializers.FileUploadAnswerDocumentSerializer'
    }


# This can't be in serializers because of circular imports
class BaseActivitySerializer(ModelSerializer):
    title = serializers.CharField()
    description = RichTextField()
    status = FSMField(read_only=True)
    owner = ResourceRelatedField(read_only=True)
    categories = ResourceRelatedField(many=True, read_only=True)
    permissions = ResourcePermissionField('activity-detail', view_args=('pk',))
    transitions = AvailableTransitionsField(source='states')
    contributor_count = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    is_follower = serializers.SerializerMethodField()
    goals = ResourceRelatedField(required=False, many=True, read_only=True)
    slug = serializers.CharField(read_only=True)
    office_restriction = serializers.CharField(required=False)
    current_status = CurrentStatusField(source='states.current_state')
    admin_url = serializers.SerializerMethodField()
    partner_organization = ResourceRelatedField(
        source='organization',
        queryset=Organization.objects.all(),
        required=False,
        allow_null=True,
    )

    updates = HyperlinkedRelatedField(
        many=True,
        read_only=True,
        related_link_view_name='activity-update-list',
        related_link_url_kwarg='activity_pk',
    )

    segments = SerializerMethodResourceRelatedField(
        source='segments',
        model=Segment,
        many=True,
        read_only=True
    )

    answers = PolymorphicResourceRelatedField(
        ActivityAnswerSerializer,
        queryset=ActivityAnswer.objects.all(),
        many=True
    )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.context["request"].user

        if not (
                user in instance.owners
                or user.is_staff
                or user.is_superuser
        ):
            visible_answers = instance.answers.filter(question__visibility="all")
            field = self.fields["answers"]
            data["answers"] = field.to_representation(list(visible_answers))
        return data

    def __init__(self, instance=None, *args, **kwargs):
        super().__init__(instance, *args, **kwargs)

        if not instance or instance.status in ('draft', 'needs_work'):
            for key in self.fields:
                self.fields[key].allow_blank = True
                self.fields[key].validators = []
                self.fields[key].allow_null = True
                self.fields[key].required = False

    def get_segments(self, obj):
        return obj.segments.filter(segment_type__visibility=True)

    def get_admin_url(self, obj):
        user = get_current_user()
        if user and user.is_authenticated and (user.is_staff or user.is_superuser):
            url = reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=[obj.id])
            return url

    def get_partner_organization(self, obj):
        if obj.organization:
            return obj.organization
        elif obj.initiative and obj.initiative.organization:
            return obj.initiative.organization

    matching_properties = MatchingPropertiesField()

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'owner.avatar': 'bluebottle.initiatives.serializers.AvatarImageSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'theme': 'bluebottle.initiatives.serializers.ThemeSerializer',
        'organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
        'goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
        'goals.impact_type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
        'image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'segments': 'bluebottle.segments.serializers.SegmentListSerializer',
        'segments.segment_type': 'bluebottle.segments.serializers.SegmentTypeSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'initiative.categories': 'bluebottle.categories.serializers.CategorySerializer',
        'categories': 'bluebottle.categories.serializers.CategorySerializer',
        'initiative.activity_managers': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative.promoter': 'bluebottle.initiatives.serializers.MemberSerializer',
        'office_location': 'bluebottle.geo.serializers.OfficeSerializer',
        'office_location.subregion': 'bluebottle.offices.serializers.SubregionSerializer',
        'office_location.subregion.region': 'bluebottle.offices.serializers.RegionSerializer',
        'partner_organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
        'answers': 'bluebottle.activities.serializers.ActivityAnswerSerializer',
        'answers.segment': 'bluebottle.segments.serializers.SegmentListSerializer',
        'answers.file': 'bluebottle.files.serializers.DocumentSerializer',
        'answers.question': 'bluebottle.activities.serializers.ActivityQuestionSerializer',
    }

    def get_is_follower(self, instance):
        user = self.context['request'].user
        return bool(user.is_authenticated) and instance.followers.filter(user=user).exists()

    def get_contributor_count(self, instance):
        return instance.deleted_successful_contributors + instance.contributors.not_instance_of(Organizer).filter(
            status__in=['accepted', 'succeeded', 'activity_refunded']
        ).count()

    def get_team_count(self, instance):
        return instance.old_teams.filter(status__in=['open', 'finished']).count()

    class Meta(object):
        model = Activity
        fields = (
            'slug',
            'id',
            'image',
            'video_url',
            'initiative',
            'categories',
            'goals',
            'owner',
            'title',
            'description',
            'is_follower',
            'status',
            'stats',
            'has_deleted_data',
            'errors',
            'required',
            'goals',
            'office_location',
            'office_restriction',
            'segments',
            'team_activity',
            'updates',
            'next_step_link',
            'next_step_title',
            'next_step_description',
            'next_step_button_label',
            'admin_url',
            'partner_organization',
            'theme',
            'answers',
            'tos_accepted'
        )

        meta_fields = (
            'permissions',
            'transitions',
            'created',
            'updated',
            'errors',
            'required',
            'matching_properties',
            'deleted_successful_contributors',
            'contributor_count',
            'team_count',
            'current_status',
            'admin_url'
        )

    class JSONAPIMeta(object):
        included_resources = [
            'owner',
            'owner.avatar',
            'image',
            'initiative',
            'theme',
            'goals',
            'goals.impact_type',
            'initiative.owner',
            'initiative.place',
            'initiative.location',
            'initiative.activity_managers',
            'initiative.promoter',
            'initiative.image',
            'categories',
            'initiative.categories',
            'segments',
            'segments.segment_type',
            'office_location',
            'office_location.subregion',
            'office_location.subregion.region',
            'partner_organization',
            'answers',
            'answers.segment',
            'answers.file',
            'answers.question'
        ]


class BaseActivityListSerializer(ModelSerializer):
    title = serializers.CharField(allow_blank=True, required=False)
    status = FSMField(read_only=True)
    permissions = ResourcePermissionField('activity-detail', view_args=('pk',))
    owner = ResourceRelatedField(read_only=True)
    is_follower = serializers.SerializerMethodField()
    goals = ResourceRelatedField(required=False, many=True, queryset=ImpactGoal.objects.all())
    slug = serializers.CharField(read_only=True)
    matching_properties = MatchingPropertiesField()
    team_activity = SerializerMethodField()
    current_status = CurrentStatusField(source='states.current_state')

    def get_team_activity(self, instance):
        if InitiativePlatformSettings.load().team_activities:
            return instance.team_activity
        return 'individuals'

    included_serializers = {
        'initiative': 'bluebottle.initiatives.serializers.InitiativeListSerializer',
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
            'team_activity',
            'current_status'
        )

        meta_fields = (
            'permissions',
            'created',
            'updated',
            'matching_properties',
            'current_status'
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
    user = ResourceRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    start = serializers.SerializerMethodField()

    def get_start(self, obj):
        if obj.contributions.exists():
            return obj.contributions.last().start
        return None

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.TinyActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(object):
        model = Contributor
        fields = (
            "user",
            "activity",
            "status",
            "created",
            "updated",
            "start"
        )
        meta_fields = (
            "created",
            "updated",
            "start"
        )

    class JSONAPIMeta(object):
        included_resources = [
            'user',
            'activity',
        ]
        resource_name = 'contributors'


# This can't be in serializers because of circular imports
class BaseContributorSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    user = ResourceRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    team = ResourceRelatedField(read_only=True)
    transitions = AvailableTransitionsField(source='states')
    current_status = CurrentStatusField(source='states.current_state')
    start = serializers.SerializerMethodField()
    email = serializers.CharField(write_only=True, required=False)
    send_messages = serializers.BooleanField(write_only=True, required=False)

    def get_start(self, obj):
        if obj.contributions.exists():
            return obj.contributions.last().start
        return None

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'user.avatar': 'bluebottle.initiatives.serializers.AvatarImageSerializer',
    }

    class Meta(object):
        model = Contributor
        fields = (
            'user',
            'activity',
            'status',
            'current_status',
            'start',
            'email',
            'send_messages',
        )
        meta_fields = (
            'transitions',
            'created',
            'updated',
            'start',
            'current_status',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'user',
            'user.avatar',
            'activity',
        ]
        resource_name = 'contributors'


# This can't be in serializers because of circular imports
class BaseContributionSerializer(ModelSerializer):
    status = FSMField(read_only=True)

    class Meta(object):
        model = Contribution
        fields = ("value", "status", "start", "end")
        meta_fields = ("created", 'end', 'start')

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

    contributor_count += Activity.objects.filter(id__in=ids).\
        aggregate(total=Sum('deleted_successful_contributors'))['total'] or 0

    types = CollectType.objects.all()
    collect = (
        CollectActivity.objects.filter(
            status__in=['succeeded', 'open'],
            id__in=ids
        )
        .values('collect_type_id')
        .annotate(amount=Sum('realized'))
    )

    type_dict = {int(type_obj.id): type_obj for type_obj in types}

    collected = [
        {
            'name': type_dict[int(col['collect_type_id'])].safe_translation_getter('name'),
            'value': col['amount']
        }
        for col in collect
        if col['collect_type_id']
    ]

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

    impact = []
    for type, goals in groupby(
        ImpactGoal.objects.filter(activity__in=ids).order_by('type'),
        lambda goal: goal.type
    ):
        value = sum(goal.realized or goal.realized_from_contributions or 0 for goal in goals)

        if value:
            impact.append({
                'name': type.text_passed,
                'iconName': type.icon,
                'unit': type.unit,
                'value': value
            })

    return {
        'impact': impact,
        'hours': time['value'].total_seconds() / 3600 if time['value'] else 0,
        'effort': effort['count'],
        'collected': collected,
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
        fields = ('id', 'team',)

    class JSONAPIMeta(object):
        included_resources = [
            'team', 'team.owner',
        ]

        resource_name = 'activities/invites'

    included_serializers = {
        'team': 'bluebottle.activities.utils.TeamSerializer',
        'team.owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


def bulk_add_participants(activity, emails, send_messages):
    created = 0
    added = 0
    existing = 0
    failed = 0
    Participant = None
    if isinstance(activity, Deed):
        Participant = DeedParticipant
    if isinstance(activity, CollectActivity):
        Participant = CollectContributor
    if isinstance(activity, DeadlineActivity):
        Participant = DeadlineParticipant
    if isinstance(activity, DateActivitySlot):
        Participant = DateParticipant
    if isinstance(activity, RegisteredDateActivity):
        Participant = RegisteredDateParticipant

    if not Participant:
        raise AttributeError(f'Could not find participant type for {activity}')
    new = False
    for email in emails:
        try:
            user = Member.objects.filter(email__iexact=email.strip()).first()
            settings = MemberPlatformSettings.objects.get()
            if not user:
                new = True
                if settings.closed:
                    email = email.strip()
                    try:
                        user = Member.create_by_email(email)
                        created += 1
                    except Exception:
                        failed += 1
                        continue
                else:
                    failed += 1
                    continue
            if isinstance(activity, DateActivitySlot):
                slot = activity
                participant, cr = DateParticipant.objects.get_or_create(
                    user=user,
                    activity=slot.activity,
                    slot=slot
                )
                if cr:
                    if not new:
                        added += 1
                else:
                    existing += 1
            else:
                if Participant.objects.filter(user=user, activity=activity).exists():
                    existing += 1
                else:
                    if not new:
                        added += 1
                    Participant.objects.create(
                        user=user,
                        activity=activity,
                        send_messages=send_messages
                    )
        except Exception:
            failed += 1
    return {
        'added': added,
        'existing': existing,
        'failed': failed,
        'created': created
    }
