from datetime import datetime, time

import dateutil
from django.db.models.functions import Trunc
from django.utils.timezone import now, get_current_timezone
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField, SerializerMethodResourceRelatedField, ResourceRelatedField
)
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseActivityListSerializer,
    BaseContributorSerializer, BaseContributionSerializer
)
from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.files.serializers import PrivateDocumentSerializer, PrivateDocumentField
from bluebottle.fsm.serializers import TransitionSerializer, AvailableTransitionsField
from bluebottle.time_based.models import (
    TimeBasedActivity, DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, TimeContribution, DateActivitySlot,
    SlotParticipant, Skill
)
from bluebottle.time_based.permissions import ParticipantDocumentPermission, CanExportParticipantsPermission
from bluebottle.time_based.states import ParticipantStateMachine
from bluebottle.utils.fields import ValidationErrorsField, RequiredErrorsField, FSMField
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.utils.utils import reverse_signed


class TimeBasedBaseSerializer(BaseActivitySerializer):
    review = serializers.BooleanField(required=False)
    is_online = serializers.BooleanField(required=False, allow_null=True)

    class Meta(BaseActivitySerializer.Meta):
        fields = BaseActivitySerializer.Meta.fields + (
            'capacity',
            'registration_deadline',
            'expertise',
            'review',
            'contributors'
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'expertise',
            'my_contributor',
            'my_contributor.contributions',
            'my_contributor.document',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'expertise': 'bluebottle.time_based.serializers.SkillSerializer',
            'my_contributor.contributions': 'bluebottle.time_based.serializers.TimeContributionSerializer',
        }
    )


class ActivitySlotSerializer(ModelSerializer):
    is_online = serializers.BooleanField(required=False, allow_null=True)
    permissions = ResourcePermissionField('date-slot-detail', view_args=('pk',))
    transitions = AvailableTransitionsField(source='states')
    status = FSMField(read_only=True)

    class Meta:
        fields = (
            'id',
            'activity',
            'start',
            'duration',
            'transitions',
        )
        meta_fields = (
            'status',
            'permissions',
            'transitions',
            'required',
            'errors',
            'created',
            'updated',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'activity', 'location'
        ]


class DateActivitySlotSerializer(ActivitySlotSerializer):

    participants = SerializerMethodResourceRelatedField(
        model=SlotParticipant,
        many=True,
        related_link_view_name='slot-participants',
        related_link_url_kwarg='slot_id',
        source='slot_participants'
    )

    errors = ValidationErrorsField()
    required = RequiredErrorsField()
    links = serializers.SerializerMethodField()

    def get_participants(self, obj):
        return obj.slot_participants.all()

    def get_links(self, instance):
        if instance.start and instance.duration:
            return {
                'ical': reverse_signed('slot-ical', args=(instance.pk, )),
                'google': instance.google_calendar_link,
            }
        else:
            return {}

    def get_root_meta(self, resource, many):
        if many:
            try:
                activity_id = self.context['request'].GET['activity']
                return {
                    'total': len(self.context['view'].queryset.filter(activity_id=int(activity_id))),
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
            'is_online',
            'location',
            'location_hint',
            'online_meeting_url',
            'participants',
        )

    class JSONAPIMeta(ActivitySlotSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/date-slots'

    included_serializers = {
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
    }


class DateActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('date-detail', view_args=('pk',))
    my_contributor = SerializerMethodResourceRelatedField(
        model=DateParticipant,
        read_only=True,
        source='get_my_contributor'
    )

    contributors = SerializerMethodResourceRelatedField(
        model=DateParticipant,
        many=True,
        related_link_view_name='date-participants',
        related_link_url_kwarg='activity_id'
    )

    def get_contributors(self, instance):
        user = self.context['request'].user
        return [
            contributor for contributor in instance.contributors.all() if (
                isinstance(contributor, DateParticipant) and (
                    contributor.status in [
                        ParticipantStateMachine.new.value,
                        ParticipantStateMachine.accepted.value,
                        ParticipantStateMachine.succeeded.value
                    ] or
                    user in (instance.owner, instance.initiative.owner, contributor.user)
                )
            )
        ]

    participants_export_url = PrivateFileSerializer(
        'date-participant-export',
        url_args=('pk', ),
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
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'links',
            'my_contributor',
            'slot_selection',
            'preparation',
            'participants_export_url'
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/dates'
        included_resources = TimeBasedBaseSerializer.JSONAPIMeta.included_resources + [
            'my_contributor',
            'my_contributor.slots',
        ]

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'my_contributor': 'bluebottle.time_based.serializers.DateParticipantSerializer',
            'my_contributor.slots': 'bluebottle.time_based.serializers.SlotParticipantSerializer',
        }
    )


class PeriodActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('period-detail', view_args=('pk',))

    my_contributor = SerializerMethodResourceRelatedField(
        model=PeriodParticipant,
        read_only=True,
        source='get_my_contributor'
    )

    contributors = SerializerMethodResourceRelatedField(
        model=PeriodParticipant,
        many=True,
        related_link_view_name='period-participants',
        related_link_url_kwarg='activity_id'

    )

    def get_contributors(self, instance):
        user = self.context['request'].user
        return [
            contributor for contributor in instance.contributors.all() if (
                isinstance(contributor, PeriodParticipant) and (
                    contributor.status in [
                        ParticipantStateMachine.new.value,
                        ParticipantStateMachine.accepted.value,
                        ParticipantStateMachine.succeeded.value
                    ] or
                    user in (instance.owner, instance.initiative.owner, contributor.user)
                )
            )
        ]

    participants_export_url = PrivateFileSerializer(
        'period-participant-export',
        url_args=('pk', ),
        filename='participant.csv',
        permission=CanExportParticipantsPermission,
        read_only=True
    )

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
        ]

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'my_contributor': 'bluebottle.time_based.serializers.PeriodParticipantSerializer'
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


class PeriodTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=PeriodActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.PeriodActivitySerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/time-based/period-transitions'


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


class DateActivityListSerializer(TimeBasedActivityListSerializer):
    permissions = ResourcePermissionField('date-detail', view_args=('pk',))

    date_info = serializers.SerializerMethodField()
    location_info = serializers.SerializerMethodField()

    def get_filtered_slots(self, obj, only_upcoming=False):

        start = self.context['request'].GET.get('filter[start]')
        end = self.context['request'].GET.get('filter[end]')
        tz = get_current_timezone()

        slots = obj.slots.all()
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
        slots = self.get_filtered_slots(obj, True)
        starts = set(
            slots.annotate(date=Trunc('start', kind='day')).values_list('date')
        )

        return {
            'count': len(starts),
            'first': min(starts)[0].date() if starts else None,
        }

    def get_location_info(self, obj):
        slots = self.get_filtered_slots(obj, True)

        locations = slots.values_list('is_online', 'location__locality', 'location__country__alpha2_code')
        location_names = [
            '{}, {}'.format(
                location[1],
                location[2]
            ) for location in locations if location[1] or location[2]
        ]

        return {
            'is_online': all(location[0] for location in locations) if locations else False,
            'location': location_names[0] if len(set(location_names)) == 1 else None,
            'has_multiple': any(location[0] for location in locations) or len(set(location_names)) > 1
        }

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
        fields = BaseContributorSerializer.Meta.fields + ('total_duration', )

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/participants'
        included_resources = [
            'user',
            'activity',
        ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class DateParticipantListSerializer(ParticipantListSerializer):

    class Meta(ParticipantListSerializer.Meta):
        model = DateParticipant

    class JSONAPIMeta(ParticipantListSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-participants'


class PeriodParticipantListSerializer(ParticipantListSerializer):
    class Meta(ParticipantListSerializer.Meta):
        model = PeriodParticipant

    class JSONAPIMeta(ParticipantListSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/period-participants'


class ParticipantSerializer(BaseContributorSerializer):
    motivation = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    document = PrivateDocumentField(required=False, allow_null=True, permissions=[ParticipantDocumentPermission])

    activity = PolymorphicResourceRelatedField(
        TimeBasedActivitySerializer,
        queryset=TimeBasedActivity.objects.all()
    )

    def to_representation(self, instance):
        result = super().to_representation(instance)

        user = self.context['request'].user
        if user not in [
            instance.user,
            instance.activity.owner,
        ] and user not in instance.activity.initiative.activity_managers.all():
            del result['motivation']
            del result['document']

        return result

    class Meta(BaseContributorSerializer.Meta):
        model = DateParticipant
        fields = BaseContributorSerializer.Meta.fields + (
            'motivation',
            'document',
            'contributions',
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
            'document',
        ]

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class DateParticipantSerializer(ParticipantSerializer):

    permissions = ResourcePermissionField('date-participant-detail', view_args=('pk',))

    class Meta(ParticipantSerializer.Meta):
        model = DateParticipant
        meta_fields = ParticipantSerializer.Meta.meta_fields + ('permissions', )

        validators = [
            UniqueTogetherValidator(
                queryset=DateParticipant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-participants'

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            'document': 'bluebottle.time_based.serializers.DateParticipantDocumentSerializer',
        }
    )


class PeriodParticipantSerializer(ParticipantSerializer):
    permissions = ResourcePermissionField('period-participant-detail', view_args=('pk',))
    contributions = ResourceRelatedField(read_only=True, many=True)

    class Meta(ParticipantSerializer.Meta):
        model = PeriodParticipant

        meta_fields = ParticipantSerializer.Meta.meta_fields + ('permissions', )

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
        ]

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            'document': 'bluebottle.time_based.serializers.PeriodParticipantDocumentSerializer',
            'contributions': 'bluebottle.time_based.serializers.TimeContributionSerializer',
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

    class Meta:
        model = SlotParticipant
        fields = ['id', 'slot', 'participant']
        meta_fields = ('status', 'transitions', )

        validators = [
            UniqueTogetherValidator(
                queryset=SlotParticipant.objects.all(),
                fields=('slot', 'participant')
            ),
            activity_matches_participant_and_slot
        ]

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/slot-participants'
        included_resources = [
            'participant',
            'slot',
            'participant.user'
        ]

    included_serializers = {
        'participant.user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'participant': 'bluebottle.time_based.serializers.DateParticipantSerializer',
        'slot': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
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

        meta_fields = BaseContributionSerializer.Meta.meta_fields + ('permissions', )

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
    }

    class JSONAPIMeta(ParticipantTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-participant-transitions'


class PeriodParticipantTransitionSerializer(ParticipantTransitionSerializer):
    resource = ResourceRelatedField(queryset=PeriodParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.PeriodParticipantSerializer',
    }

    class JSONAPIMeta(ParticipantTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/period-participant-transitions'


class SkillSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta(object):
        model = Skill
        fields = ('id', 'name', 'expertise')

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'skills'
