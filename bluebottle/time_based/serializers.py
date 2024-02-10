from datetime import datetime, time

import dateutil
from django.db.models.functions import Trunc
from django.utils.timezone import now, get_current_timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField, SerializerMethodResourceRelatedField, ResourceRelatedField,
    HyperlinkedRelatedField, SerializerMethodHyperlinkedRelatedField

)
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.activities.models import Team, Organizer
from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseActivityListSerializer,
    BaseContributorSerializer, BaseContributionSerializer
)
from bluebottle.bb_accounts.models import BlueBottleBaseUser
from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.files.serializers import PrivateDocumentSerializer, PrivateDocumentField
from bluebottle.fsm.serializers import TransitionSerializer, AvailableTransitionsField, CurrentStatusField
from bluebottle.geo.models import Geolocation
from bluebottle.time_based.models import (
    DeadlineActivity, DeadlineParticipant, TimeBasedActivity, DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, TimeContribution, DateActivitySlot,
    SlotParticipant, Skill, TeamSlot
)
from bluebottle.time_based.permissions import ParticipantDocumentPermission, CanExportParticipantsPermission
from bluebottle.time_based.states import ParticipantStateMachine
from bluebottle.utils.fields import ValidationErrorsField, RequiredErrorsField, FSMField
from bluebottle.utils.serializers import ResourcePermissionField, AnonymizedResourceRelatedField
from bluebottle.utils.utils import reverse_signed


class TeamsField(HyperlinkedRelatedField):
    def __init__(self, many=True, read_only=True, *args, **kwargs):
        super().__init__(Team, many=many, read_only=read_only, *args, **kwargs)

    def get_url(self, name, view_name, kwargs, request):
        if self.parent.instance.team_activity == 'teams':
            return f"{self.reverse('team-list')}?filter[activity_id]={kwargs['pk']}"


class UnreviewedContributorsField(SerializerMethodHyperlinkedRelatedField):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model')
        super().__init__(*args, **kwargs)

    def get_url(self, *args, **kwargs):
        url = super().get_url(*args, **kwargs)

        if url:
            return f"{url}?filter[status]=new"


class TimeBasedBaseSerializer(BaseActivitySerializer):
    review = serializers.BooleanField(required=False, allow_null=True)
    is_online = serializers.BooleanField(required=False, allow_null=True)

    teams = TeamsField()

    class Meta(BaseActivitySerializer.Meta):
        fields = BaseActivitySerializer.Meta.fields + (
            'capacity',
            'registration_deadline',
            'expertise',
            'review',
            'registration_flow',
            'review_link',
            'review_title',
            'review_description',
            'review_document_enabled',
            'contributors',
            'unreviewed_contributors',
            'my_contributor',
            'teams',
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'expertise',
            'my_contributor',
            'my_contributor.user',
            'my_contributor.contributions',
            'my_contributor.document',
            'my_contributor.invite',
            'my_contributor.team',
            'my_contributor.team.owner',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'expertise': 'bluebottle.time_based.serializers.SkillSerializer',
            'my_contributor.contributions': 'bluebottle.time_based.serializers.TimeContributionSerializer',
            'my_contributor.user': 'bluebottle.initiatives.serializers.MemberSerializer',
            'my_contributor.invite': 'bluebottle.activities.utils.InviteSerializer',
            'my_contributor.team': 'bluebottle.activities.utils.TeamSerializer',
            'my_contributor.team.owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        }
    )


class ActivitySlotSerializer(ModelSerializer):
    is_online = serializers.BooleanField(required=False, allow_null=True)
    permissions = ResourcePermissionField('date-slot-detail', view_args=('pk',))
    transitions = AvailableTransitionsField(source='states')
    status = FSMField(read_only=True)
    location = ResourceRelatedField(queryset=Geolocation.objects, required=False, allow_null=True)
    current_status = CurrentStatusField(source='states.current_state')

    my_contributor = SerializerMethodResourceRelatedField(
        model=SlotParticipant,
        read_only=True,
    )

    participants_export_url = PrivateFileSerializer(
        'slot-participant-export',
        url_args=('pk',),
        filename='participant.csv',
        permission=CanExportParticipantsPermission,
        read_only=True
    )

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.slot_participants.filter(participant__user=user).first()

    class Meta:
        fields = (
            'id',
            'activity',
            'start',
            'end',
            'transitions',
            'is_online',
            'location_hint',
            'online_meeting_url',
            'my_contributor',
            'location',
            'participants_export_url'
        )
        meta_fields = (
            'status',
            'current_status',
            'contributor_count',
            'permissions',
            'transitions',
            'required',
            'errors',
            'created',
            'updated',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'activity',
            'location',
            'my_contributor',
        ]

    included_serializers = {
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
        'my_contributor': 'bluebottle.time_based.serializers.SlotParticipantSerializer',
    }


class DateActivitySlotSerializer(ActivitySlotSerializer):
    participants = HyperlinkedRelatedField(
        read_only=True,
        many=True,
        related_link_view_name='slot-participants',
        related_link_url_kwarg='slot_id',
        source='slot_participants'
    )

    errors = ValidationErrorsField()
    required = RequiredErrorsField()
    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        if instance.start and instance.duration:
            return {
                'ical': reverse_signed('slot-ical', args=(instance.pk,)),
                'google': instance.google_calendar_link,
            }
        else:
            return {}

    def get_root_meta(self, resource, many):
        if many:
            try:
                activity_id = self.context['request'].GET['activity']
                queryset = self.context['view'].queryset.filter(
                    activity_id=int(activity_id)
                ).order_by('start')

                try:
                    contributor_id = self.context['request'].GET['contributor']
                    queryset = queryset.filter(
                        slot_participants__status__in=['registered', 'succeeded'],
                        slot_participants__participant_id=contributor_id
                    )
                except KeyError:
                    pass

                first = queryset.first()
                return {
                    'first': first.start if first else None,
                    'total': len(queryset),
                }
            except (KeyError, ValueError):
                pass

        return {}

    class Meta(ActivitySlotSerializer.Meta):
        model = DateActivitySlot
        fields = ActivitySlotSerializer.Meta.fields + (
            'title',
            'start',
            'links',
            'duration',
            'capacity',
            'participants',
        )

    class JSONAPIMeta(ActivitySlotSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/date-slots'
        included_resources = ['activity', 'my_contributor', 'my_contributor.participant.user', 'location']

    included_serializers = dict(
        ActivitySlotSerializer.included_serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'my_contributor': 'bluebottle.time_based.serializers.SlotParticipantSerializer',
            'my_contributor.participant.user': 'bluebottle.initiatives.serializers.MemberSerializer',
        }
    )


class TeamSlotSerializer(ActivitySlotSerializer):
    activity = ResourceRelatedField(read_only=True)
    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        if instance.start and instance.duration:
            return {
                'ical': reverse_signed('team-ical', args=(instance.pk,)),
                'google': instance.google_calendar_link,
            }
        else:
            return {}

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.team.members.filter(periodparticipant__user=user).first()

    class Meta(ActivitySlotSerializer.Meta):
        model = TeamSlot
        fields = ActivitySlotSerializer.Meta.fields + (
            'team',
            'start',
            'duration',
            'location',
            'links'
        )
        meta_fields = (
            'status',
            'permissions',
            'transitions',
            'created',
            'updated',
        )

    class JSONAPIMeta(object):
        resource_name = 'activities/time-based/team-slots'
        included_resources = [
            'activity'
            'team',
            'location'
        ]

    included_serializers = {
        'team': 'bluebottle.activities.utils.TeamSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'activity': 'bluebottle.time_based.serializers.PeriodActivitySerializer',
    }


class DateActivitySlotInfoMixin():
    def get_filtered_slots(self, obj, only_upcoming=False):

        start = self.context['request'].GET.get('filter[start]')
        end = self.context['request'].GET.get('filter[end]')
        tz = get_current_timezone()

        slots = obj.slots.exclude(status__in=['draft', 'cancelled']).all()
        try:
            if start:
                slots = slots.filter(start__gte=dateutil.parser.parse(start).astimezone(tz))
            elif only_upcoming:
                slots = slots.filter(start__gte=now())

            if end:
                slots = slots.filter(
                    start__lte=datetime.combine(dateutil.parser.parse(end), time.max).astimezone(tz)
                )
        except ValueError:
            pass

        return slots

    def get_date_info(self, obj):
        total = self.get_filtered_slots(obj).count()
        slots = self.get_filtered_slots(obj, only_upcoming=True)
        last_slot = obj.slots.exclude(status__in=['draft', 'cancelled']).order_by('start').last()
        end = last_slot.end if last_slot else None
        capacity = None
        duration = None

        if total > 1:
            starts = set(
                slots.annotate(date=Trunc('start', kind='day')).values_list('date')
            )
            count = len(slots)
            end = end.date()
            first = min(starts)[0].date() if starts else None
        elif total == 1:
            slot = self.get_filtered_slots(obj).first()
            first = slot.start
            duration = slot.duration
            count = 1
        else:
            first = None
            duration = None
            count = 0

        return {
            'total': total,
            'has_multiple': total > 1,
            'is_full': all(slot.status == 'full' for slot in slots),
            'count': count,
            'first': first,
            'end': end,
            'duration': duration,
            'capacity': capacity,
        }

    def get_location_info(self, obj):
        slots = self.get_filtered_slots(obj, only_upcoming=False)
        is_online = len(slots) > 0 and len(slots.filter(is_online=True)) == len(slots)

        locations = slots.values_list(
            'location__locality',
            'location__country__alpha2_code',
            'location__formatted_address',
            'online_meeting_url',
            'location_hint'
        )

        if not len(slots) or not len(locations):
            return {
                'has_multiple': False,
                'is_online': is_online,
                'online_meeting_url': None,
                'location': None,
                'location_hint': None,
            }

        has_multiple = len(set(location[:2] for location in locations)) > 1 and not is_online
        if has_multiple:
            return {
                'has_multiple': True,
                'is_online': False,
                'online_meeting_url': None,
                'location': None,
                'location_hint': None,
            }
        slot = slots.first()

        if is_online or not slot.location:
            location = None
        else:
            location = {
                'locality': slot.location.locality if slot.location else None,
                'country': {
                    'code': slot.location.country.alpha2_code if slot.location.country else None,
                },
                'formattedAddress': slot.location.formatted_address if slot.location else None,
            }

        user = self.context['request'].user
        if (
                user.is_authenticated and
                obj.contributors.filter(user=user, status='accepted').instance_of(DateParticipant).count()
        ):
            meeting_url = slot.online_meeting_url or None
        else:
            meeting_url = None

        return {
            'has_multiple': False,
            'is_online': is_online,
            'online_meeting_url': meeting_url,
            'location': location,
            'location_hint': slot.location_hint,
        }


class DateActivitySerializer(DateActivitySlotInfoMixin, TimeBasedBaseSerializer):
    date_info = serializers.SerializerMethodField()
    location_info = serializers.SerializerMethodField()
    slot_count = serializers.SerializerMethodField()

    slots = HyperlinkedRelatedField(
        many=True,
        read_only=True,
        related_link_view_name='date-slots',
        related_link_url_kwarg='pk',
    )

    permissions = ResourcePermissionField('date-detail', view_args=('pk',))
    my_contributor = SerializerMethodResourceRelatedField(
        model=DateParticipant,
        read_only=True,
        source='get_my_contributor'
    )

    contributors = SerializerMethodHyperlinkedRelatedField(
        model=DateParticipant,
        read_only=True,
        many=True,
        related_link_view_name='date-participants',
        related_link_url_kwarg='activity_id'
    )

    unreviewed_contributors = UnreviewedContributorsField(
        read_only=True,
        related_link_view_name='date-participants',
        related_link_url_kwarg='activity_id',
        model=DateParticipant
    )

    first_slot = SerializerMethodResourceRelatedField(
        model=DateActivitySlot,
        read_only=True,
        source='get_first_slot'
    )

    def get_contributor_count(self, instance):
        return instance.deleted_successful_contributors + instance.contributors.not_instance_of(Organizer).filter(
            status__in=['accepted', 'succeeded'],
            dateparticipant__slot_participants__status='registered'
        ).count()

    def get_first_slot(self, instance):
        return instance.slots.filter(
            start__gte=now()
        ).exclude(status__in=['draft', 'cancelled']).order_by('start').first()

    def get_slot_count(self, instance):
        return len(instance.slots.all())

    def get_contributors(self, instance):
        user = self.context['request'].user
        return [
            contributor for contributor in instance.contributors.all() if (
                isinstance(contributor, DateParticipant) and (
                    contributor.status in [
                        ParticipantStateMachine.new.value,
                        ParticipantStateMachine.accepted.value,
                        ParticipantStateMachine.succeeded.value
                    ] or user in (instance.owner, instance.initiative.owner, contributor.user)
                )
            )
        ]

    def get_unreviewed_contributors(self, instance):
        user = self.context['request'].user
        unreviewed_participants = instance.contributors.instance_of(
            DateParticipant
        ).filter(
            status=ParticipantStateMachine.new.value
        )

        if (
                user not in (instance.owner, instance.initiative.owner) and
                user not in instance.activity_managers.all()
        ):
            unreviewed_participants = unreviewed_participants.filter(user=user)

        return unreviewed_participants

    participants_export_url = PrivateFileSerializer(
        'date-participant-export',
        url_args=('pk',),
        filename='participant.csv',
        permission=CanExportParticipantsPermission,
        read_only=True
    )

    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        user = self.context['request'].user

        user_id = user.pk if user.is_authenticated else 0
        return {
            'ical': reverse_signed('date-ical', args=(instance.pk, user_id)),
        }

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.contributors.filter(user=user).instance_of(DateParticipant).first()

    class Meta(TimeBasedBaseSerializer.Meta):
        model = DateActivity
        meta_fields = TimeBasedBaseSerializer.Meta.meta_fields + ('slot_count',)
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'links',
            'my_contributor',
            'slot_selection',
            'preparation',
            'participants_export_url',
            'date_info',
            'location_info',
            'slots',
            'first_slot',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/dates'
        included_resources = TimeBasedBaseSerializer.JSONAPIMeta.included_resources + [
            'my_contributor',
            'my_contributor.user',
            'my_contributor.location',
            'first_slot',
        ]

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'my_contributor': 'bluebottle.time_based.serializers.DateParticipantSerializer',
            'my_contributor.user': 'bluebottle.initiatives.serializers.MemberSerializer',
            'first_slot': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
        }
    )


class ParticipantsField(HyperlinkedRelatedField):
    def __init__(self, many=True, read_only=True, *args, **kwargs):
        super().__init__(
            many=many,
            read_only=read_only,
            related_link_view_name='period-participants',
            related_link_url_kwarg='activity_id',
        )

    def get_url(self, name, view_name, kwargs, request):
        if self.parent.instance.team_activity != 'teams':
            return super().get_url(name, view_name, kwargs, request)


class PeriodActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('period-detail', view_args=('pk',))

    my_contributor = SerializerMethodResourceRelatedField(
        model=PeriodParticipant,
        read_only=True,
        source='get_my_contributor'
    )

    contributors = SerializerMethodHyperlinkedRelatedField(
        model=PeriodParticipant,
        read_only=True,
        many=True,
        related_link_view_name='period-participants',
        related_link_url_kwarg='activity_id'
    )

    unreviewed_contributors = UnreviewedContributorsField(
        read_only=True,
        related_link_view_name='period-participants',
        related_link_url_kwarg='activity_id',
        model=PeriodParticipant
    )

    participants_export_url = PrivateFileSerializer(
        'period-participant-export',
        url_args=('pk',),
        filename='participant.csv',
        permission=CanExportParticipantsPermission,
        read_only=True
    )

    def get_unreviewed_contributors(self, instance):
        user = self.context['request'].user
        unreviewed_participants = instance.contributors.instance_of(
            PeriodParticipant
        ).filter(
            status=ParticipantStateMachine.new.value
        )

        if (
            user not in (instance.owner, instance.initiative.owner) and
            user not in instance.activity_managers.all()
        ):
            unreviewed_participants = unreviewed_participants.filter(user=user)

        return unreviewed_participants

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.contributors.filter(user=user).instance_of(PeriodParticipant).first()

    class Meta(TimeBasedBaseSerializer.Meta):
        model = PeriodActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start',
            'deadline',
            'duration',
            'duration_period',
            'my_contributor',
            'online_meeting_url',
            'is_online',
            'location',
            'location_hint',
            'participants_export_url'
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/periods'
        included_resources = TimeBasedBaseSerializer.JSONAPIMeta.included_resources + [
            'location',
            'my_contributor.team',
            'my_contributor.team.slot',
            'my_contributor.team.slot.location',
        ]

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'my_contributor': 'bluebottle.time_based.serializers.PeriodParticipantSerializer',
            'my_contributor.team': 'bluebottle.activities.utils.TeamSerializer',
            'my_contributor.team.slot': 'bluebottle.time_based.serializers.TeamSlotSerializer',
            'my_contributor.team.slot.location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class DeadlineActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('deadline-detail', view_args=('pk',))

    my_contributor = SerializerMethodResourceRelatedField(
        model=PeriodParticipant,
        read_only=True,
        source='get_my_contributor'
    )

    contributors = SerializerMethodHyperlinkedRelatedField(
        model=PeriodParticipant,
        read_only=True,
        many=True,
        related_link_view_name='deadline-participants',
        related_link_url_kwarg='activity_id'
    )

    unreviewed_contributors = UnreviewedContributorsField(
        read_only=True,
        related_link_view_name='deadline-participants',
        related_link_url_kwarg='activity_id',
        model=PeriodParticipant
    )

    participants_export_url = PrivateFileSerializer(
        'deadline-participant-export',
        url_args=('pk',),
        filename='participant.csv',
        permission=CanExportParticipantsPermission,
        read_only=True
    )

    def get_unreviewed_contributors(self, instance):
        user = self.context['request'].user
        unreviewed_participants = instance.contributors.instance_of(
            DeadlineParticipant
        ).filter(
            status=ParticipantStateMachine.new.value
        )

        if (
            user not in (instance.owner, instance.initiative.owner) and
            user not in instance.activity_managers.all()
        ):
            unreviewed_participants = unreviewed_participants.filter(user=user)

        return unreviewed_participants

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.contributors.filter(user=user).instance_of(DeadlineParticipant).first()

    class Meta(TimeBasedBaseSerializer.Meta):
        model = DeadlineActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start',
            'deadline',
            'duration',
            'my_contributor',
            'online_meeting_url',
            'is_online',
            'location',
            'location_hint',
            'participants_export_url',
            'registration_flow',
            'review_link',
            'review_title',
            'review_description',
            'review_document_enabled',

        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/deadlines'
        included_resources = TimeBasedBaseSerializer.JSONAPIMeta.included_resources + [
            'location',
        ]

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class TimeBasedActivitySerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DateActivitySerializer,
        PeriodActivitySerializer,
    ]

    class Meta(object):
        model = TimeBasedActivity
        meta_fields = (
            'permissions',
            'transitions',
            'created',
            'updated',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'owner',
            'initiative',
            'location',
            'image',
            'goals',
            'goals.type',
            'initiative.image',
            'initiative.place',
        ]


class DateTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DateActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DateActivitySerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/time-based/date-transitions'


class DateSlotTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DateActivitySlot.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/time-based/slot-transitions'


class PeriodTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=PeriodActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.PeriodActivitySerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/time-based/period-transitions'


class DeadlineTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DeadlineActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/time-based/deadline-transitions'


class TimeBasedActivityListSerializer(BaseActivityListSerializer):
    class Meta(BaseActivityListSerializer.Meta):
        fields = BaseActivityListSerializer.Meta.fields + (
            'capacity',
            'expertise',
            'registration_deadline',
        )

    class JSONAPIMeta(BaseActivityListSerializer.JSONAPIMeta):
        included_resources = [
            'expertise',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'expertise': 'bluebottle.time_based.serializers.SkillSerializer',
        }
    )


class DateActivityListSerializer(DateActivitySlotInfoMixin, TimeBasedActivityListSerializer):
    date_info = serializers.SerializerMethodField()
    location_info = serializers.SerializerMethodField()

    permissions = ResourcePermissionField('date-detail', view_args=('pk',))

    class Meta(TimeBasedActivityListSerializer.Meta):
        model = DateActivity
        fields = TimeBasedActivityListSerializer.Meta.fields + (
            'location_info', 'date_info',
        )

    class JSONAPIMeta(TimeBasedActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/dates'
        included_resources = TimeBasedActivityListSerializer.JSONAPIMeta.included_resources + ['slots']

    included_serializers = dict(
        TimeBasedActivityListSerializer.included_serializers,
        **{
            'slots': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
        }
    )


class PeriodActivityListSerializer(TimeBasedActivityListSerializer):
    permissions = ResourcePermissionField('period-detail', view_args=('pk',))

    class Meta(TimeBasedActivityListSerializer.Meta):
        model = PeriodActivity
        fields = TimeBasedActivityListSerializer.Meta.fields + (
            'start', 'deadline', 'duration', 'duration_period', 'location', 'is_online',
        )

    class JSONAPIMeta(TimeBasedActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/period'

    included_serializers = dict(
        TimeBasedActivityListSerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class DateParticipantDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'date-participant-document'
    relationship = 'dateparticipant_set'


class PeriodParticipantDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'period-participant-document'
    relationship = 'periodparticipant_set'


class ParticipantListSerializer(BaseContributorSerializer):
    activity = PolymorphicResourceRelatedField(
        TimeBasedActivitySerializer,
        queryset=TimeBasedActivity.objects.all()
    )
    total_duration = serializers.DurationField(read_only=True)

    class Meta(BaseContributorSerializer.Meta):
        fields = BaseContributorSerializer.Meta.fields + ('total_duration',)

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/participants'


class DateParticipantListSerializer(ParticipantListSerializer):
    slots = ResourceRelatedField(
        source='slot_participants',
        many=True,
        read_only=True
    )

    class Meta(ParticipantListSerializer.Meta):
        model = DateParticipant
        fields = ParticipantListSerializer.Meta.fields + ('slots',)

    class JSONAPIMeta(ParticipantListSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-participants'
        included_resources = ParticipantListSerializer.JSONAPIMeta.included_resources + [
            'slots',
            'slots.slot'
        ]

    included_serializers = dict(
        ParticipantListSerializer.included_serializers,
        **{
            'slots': 'bluebottle.time_based.serializers.SlotParticipantSerializer',
            'slots.slot': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
        }
    )


class PeriodParticipantListSerializer(ParticipantListSerializer):
    class Meta(ParticipantListSerializer.Meta):
        model = PeriodParticipant

    class JSONAPIMeta(ParticipantListSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/period-participants'


class ParticipantSerializer(BaseContributorSerializer):
    motivation = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    document = PrivateDocumentField(required=False, allow_null=True, permissions=[ParticipantDocumentPermission])

    def to_representation(self, instance):
        result = super().to_representation(instance)

        user = self.context['request'].user
        if (user not in [
            instance.user,
            instance.activity.owner,
        ] and user not in instance.activity.initiative.activity_managers.all() and
            not user.is_staff and
            not user.is_superuser
        ):
            del result['motivation']
            del result['document']

        return result

    class Meta(BaseContributorSerializer.Meta):
        model = DateParticipant
        fields = BaseContributorSerializer.Meta.fields + (
            'motivation',
            'document',
            'invite',
            'team'
        )

        validators = [
            UniqueTogetherValidator(
                queryset=DateParticipant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/participants'
        included_resources = [
            'user',
            'invite',
            'document',
            'team'
        ]


class TeamMemberSerializer(BaseContributorSerializer):
    activity = PolymorphicResourceRelatedField(
        TimeBasedActivitySerializer,
        queryset=TimeBasedActivity.objects.all()
    )

    class Meta(BaseContributorSerializer.Meta):
        model = PeriodParticipant
        fields = (
            'user',
            'status',
            'team',
            'accepted_invite',
            'invite',
            'team',
            'activity'
        )

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/period-participants'
        included_resources = BaseContributorSerializer.JSONAPIMeta.included_resources + [
            'contributions',
            'team',
            'team.slot',
        ]

    included_serializers = dict(
        BaseContributorSerializer.included_serializers,
        **{
            'document': 'bluebottle.time_based.serializers.PeriodParticipantDocumentSerializer',
            'contributions': 'bluebottle.time_based.serializers.TimeContributionSerializer',
            'team.slot': 'bluebottle.time_based.serializers.TeamSlotSerializer',
        }
    )


class DateParticipantSerializer(ParticipantSerializer):
    slot_count = serializers.SerializerMethodField()

    slot_participants = HyperlinkedRelatedField(
        many=True,
        read_only=True,
        related_link_view_name='related-slot-participant-list',
        related_link_url_kwarg='participant_id',
    )

    permissions = ResourcePermissionField('date-participant-detail', view_args=('pk',))

    def get_slot_count(self, obj):
        return obj.slot_participants.count()

    class Meta(ParticipantSerializer.Meta):
        model = DateParticipant
        meta_fields = ParticipantSerializer.Meta.meta_fields + ('permissions', 'slot_count')
        fields = ParticipantSerializer.Meta.fields + ('slot_participants', )
        validators = [
            UniqueTogetherValidator(
                queryset=DateParticipant.objects.all(),
                fields=('activity', 'user',)
            )
        ]

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-participants'
        included_resources = ParticipantSerializer.JSONAPIMeta.included_resources + [
            'activity',
        ]

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            'user': 'bluebottle.initiatives.serializers.MemberSerializer',
            'document': 'bluebottle.time_based.serializers.DateParticipantDocumentSerializer',
            'activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
        }
    )


class PeriodParticipantSerializer(ParticipantSerializer):
    permissions = ResourcePermissionField('period-participant-detail', view_args=('pk',))

    contributions = SerializerMethodResourceRelatedField(
        model=TimeContribution,
        many=True,
        read_only=True,
    )

    def get_contributions(self, obj):
        if obj.activity.duration_period == 'overall':
            return obj.contributions.all()

    class Meta(ParticipantSerializer.Meta):
        model = PeriodParticipant

        meta_fields = ParticipantSerializer.Meta.meta_fields + ('permissions',)
        fields = ParticipantSerializer.Meta.fields + (
            'contributions',
        )

        validators = [
            UniqueTogetherValidator(
                queryset=PeriodParticipant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/period-participants'
        included_resources = ParticipantSerializer.JSONAPIMeta.included_resources + [
            'contributions',
            'team',
            'team.slot'
        ]

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            'document': 'bluebottle.time_based.serializers.PeriodParticipantDocumentSerializer',
            'contributions': 'bluebottle.time_based.serializers.TimeContributionSerializer',
            'team.slot': 'bluebottle.time_based.serializers.TeamSlotSerializer',
            'activity': 'bluebottle.time_based.serializers.PeriodActivitySerializer',
        }
    )


class DeadlineParticipantSerializer(ParticipantSerializer):
    permissions = ResourcePermissionField('deadline-participant-detail', view_args=('pk',))

    contributions = SerializerMethodResourceRelatedField(
        model=TimeContribution,
        many=True,
        read_only=True,
    )

    def get_contributions(self, obj):
        if obj.activity.duration_period == 'overall':
            return obj.contributions.all()

    class Meta(ParticipantSerializer.Meta):
        model = DeadlineParticipant

        meta_fields = ParticipantSerializer.Meta.meta_fields + ('permissions',)
        fields = ParticipantSerializer.Meta.fields + (
            'contributions',
        )

        validators = [
            UniqueTogetherValidator(
                queryset=DeadlineParticipant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/deadline-participants'
        included_resources = ParticipantSerializer.JSONAPIMeta.included_resources + [
            'contributions',
            'team',
            'team.slot'
        ]

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            'document': 'bluebottle.time_based.serializers.PeriodParticipantDocumentSerializer',
            'contributions': 'bluebottle.time_based.serializers.TimeContributionSerializer',
            'team.slot': 'bluebottle.time_based.serializers.TeamSlotSerializer',
            'activity': 'bluebottle.time_based.serializers.PeriodActivitySerializer',
        }
    )


def activity_matches_participant_and_slot(value):
    if value['slot'].activity != value['participant'].activity:
        raise serializers.ValidationError(
            'The activity of the slot does not match the activity of the participant.'
        )


class SlotParticipantSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    transitions = AvailableTransitionsField(source='states')
    current_status = CurrentStatusField(source='states.current_state')
    permissions = ResourcePermissionField('slot-participant-detail', view_args=('pk',))
    user = AnonymizedResourceRelatedField(
        read_only=True,
        model=BlueBottleBaseUser,
        default=serializers.CurrentUserDefault()
    )
    slot = ResourceRelatedField(queryset=DateActivitySlot.objects)

    def validate(self, data):
        if data['slot'].status != 'open':
            raise ValidationError('Participants cannot sign up for full slots')
        return data

    class Meta:
        model = SlotParticipant
        fields = ['id', 'participant', 'current_status', 'user', 'slot']
        meta_fields = ('status', 'transitions', 'current_status', 'permissions')

        validators = []

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/slot-participants'
        included_resources = [
            'participant',
            'slot',
            'slot.activity',
        ]

    included_serializers = {
        'participant': 'bluebottle.time_based.serializers.DateParticipantSerializer',
        'slot': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
        'slot.activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
    }


class SlotParticipantTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=SlotParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.SlotParticipantSerializer',
        'resource.participant': 'bluebottle.time_based.serializers.DateParticipantSerializer',
        'resource.slot': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', 'resource.slot', 'resource.participant']
        resource_name = 'contributors/time-based/slot-participant-transitions'


class TimeContributionSerializer(BaseContributionSerializer):
    permissions = ResourcePermissionField('time-contribution-detail', view_args=('pk',))

    class Meta(BaseContributionSerializer.Meta):
        model = TimeContribution

        meta_fields = BaseContributionSerializer.Meta.meta_fields + ('permissions',)

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-contributions'


class ParticipantTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DateParticipant.objects.all())
    field = 'states'

    class JSONAPIMeta(object):
        resource_name = 'contributors/time-based/participant-transitions'
        included_resources = [
            'resource',
        ]


class DateParticipantTransitionSerializer(ParticipantTransitionSerializer):
    resource = ResourceRelatedField(queryset=DateParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DateParticipantSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
    }

    class JSONAPIMeta(ParticipantTransitionSerializer.JSONAPIMeta):
        included_resources = [
            'resource',
            'resource.activity'
        ]
        resource_name = 'contributors/time-based/date-participant-transitions'


class PeriodParticipantTransitionSerializer(ParticipantTransitionSerializer):
    resource = ResourceRelatedField(queryset=PeriodParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.PeriodParticipantSerializer',
        'resource.team': 'bluebottle.activities.utils.TeamSerializer',
    }

    class JSONAPIMeta(ParticipantTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/period-participant-transitions'
        included_resources = ['resource', 'resource.team']


class SkillSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta(object):
        model = Skill
        fields = ('id', 'name', 'expertise')

    class JSONAPIMeta(object):
        included_resources = ['resource']
        resource_name = 'skills'
