from bluebottle.utils.fields import ValidationErrorsField, RequiredErrorsField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import ResourceRelatedField

from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField, SerializerMethodResourceRelatedField
)

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseActivityListSerializer,
    BaseContributorSerializer, BaseContributionSerializer
)

from bluebottle.files.serializers import PrivateDocumentSerializer, PrivateDocumentField
from bluebottle.fsm.serializers import TransitionSerializer, AvailableTransitionsField

from bluebottle.time_based.models import (
    TimeBasedActivity, DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, TimeContribution, DateActivitySlot
)

from bluebottle.time_based.permissions import ParticipantDocumentPermission
from bluebottle.time_based.filters import ParticipantListFilter

from bluebottle.utils.serializers import ResourcePermissionField, FilteredRelatedField
from bluebottle.utils.utils import reverse_signed


class TimeBasedBaseSerializer(BaseActivitySerializer):
    review = serializers.BooleanField(required=False)
    contributors = FilteredRelatedField(many=True, filter_backend=ParticipantListFilter)
    is_online = serializers.NullBooleanField()

    class Meta(BaseActivitySerializer.Meta):
        fields = BaseActivitySerializer.Meta.fields + (
            'capacity',
            'is_online',
            'location',
            'location_hint',
            'registration_deadline',
            'expertise',
            'review',
            'contributors'
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'location',
            'expertise',
            'my_contributor',
            'my_contributor.contributions',
            'my_contributor.document',
            'my_contributor.contributions',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'expertise': 'bluebottle.assignments.serializers.SkillSerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'my_contributor.contributions': 'bluebottle.time_based.serializers.TimeContributionSerializer',
        }
    )


class ActivitySlotSerializer(ModelSerializer):
    permissions = ResourcePermissionField('date-slot-detail', view_args=('pk',))
    transitions = AvailableTransitionsField(source='states')

    class Meta:
        fields = (
            'activity',
            'start',
            'duration',
            'transitions',
        )
        meta_fields = (
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
        ]


class DateActivitySlotSerializer(ActivitySlotSerializer):
    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    class Meta(ActivitySlotSerializer.Meta):
        model = DateActivitySlot
        fields = ActivitySlotSerializer.Meta.fields + (
            'title',
            'start',
            'duration',
            'capacity',
            'utc_offset',
            'is_online',
            'location',
            'location_hint',
            'online_meeting_url',
        )

    class JSONAPIMeta(ActivitySlotSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/date-slots'

    included_serializers = {
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'activity': 'bluebottle.time_based.serializers.DateActivityListSerializer',
    }


class DateActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('date-detail', view_args=('pk',))
    my_contributor = SerializerMethodResourceRelatedField(
        model=DateParticipant,
        read_only=True,
        source='get_my_contributor'
    )
    slots = ResourceRelatedField(many=True, required=False, queryset=DateActivitySlot.objects)
    links = serializers.SerializerMethodField()

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.contributors.filter(user=user).instance_of(DateParticipant).first()

    def get_links(self, instance):
        if instance.start and instance.duration:
            return {
                'ical': reverse_signed('date-ical', args=(instance.pk, )),
                'google': instance.google_calendar_link,
                'outlook': instance.outlook_link,
            }
        else:
            return {}

    class Meta(TimeBasedBaseSerializer.Meta):
        model = DateActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start', 'duration',
            'utc_offset',
            'online_meeting_url',
            'links',
            'my_contributor',
            'slots',
            'preparation'
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/dates'
        included_resources = TimeBasedBaseSerializer.JSONAPIMeta.included_resources + [
            'slots',
            'slots.location'
        ]

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'slots.location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'my_contributor': 'bluebottle.time_based.serializers.DateParticipantSerializer',
            'slots': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
        }
    )


class PeriodActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('period-detail', view_args=('pk',))

    my_contributor = SerializerMethodResourceRelatedField(
        model=PeriodParticipant,
        read_only=True,
        source='get_my_contributor'
    )

    contributors = FilteredRelatedField(
        many=True,
        filter_backend=ParticipantListFilter,
        related_link_view_name='period-participants',
        related_link_url_kwarg='activity_id'

    )

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.contributors.filter(user=user).instance_of(PeriodParticipant).first()

    class Meta(TimeBasedBaseSerializer.Meta):
        model = PeriodActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start', 'deadline', 'duration', 'duration_period', 'my_contributor',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/periods'

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
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
            'duration',
            'is_online',
            'location',
            'location_hint',
            'expertise',
            'registration_deadline',
        )

    class JSONAPIMeta(BaseActivityListSerializer.JSONAPIMeta):
        included_resources = [
            'location', 'expertise',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'expertise': 'bluebottle.assignments.serializers.SkillSerializer',
        }
    )


class DateActivityListSerializer(TimeBasedActivityListSerializer):
    permissions = ResourcePermissionField('date-detail', view_args=('pk',))

    class Meta(TimeBasedActivityListSerializer.Meta):
        model = DateActivity
        fields = TimeBasedActivityListSerializer.Meta.fields + (
            'start', 'duration',
        )

    class JSONAPIMeta(TimeBasedActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/dates'


class PeriodActivityListSerializer(TimeBasedActivityListSerializer):
    permissions = ResourcePermissionField('period-detail', view_args=('pk',))

    class Meta(TimeBasedActivityListSerializer.Meta):
        model = PeriodActivity
        fields = TimeBasedActivityListSerializer.Meta.fields + (
            'deadline', 'duration', 'duration_period',
        )

    class JSONAPIMeta(TimeBasedActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/period'


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
    contributions = ResourceRelatedField(read_only=True, many=True)

    def to_representation(self, instance):
        result = super().to_representation(instance)
        if self.context['request'].user not in [
            instance.user,
            instance.activity.owner,
            instance.activity.initiative.activity_manager
        ]:
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
            'contributions',
        ]

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'contributions': 'bluebottle.time_based.serializers.TimeContributionSerializer',
    }


class DateParticipantSerializer(ParticipantSerializer):
    class Meta(ParticipantSerializer.Meta):
        model = DateParticipant

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
        **{'document': 'bluebottle.time_based.serializers.DateParticipantDocumentSerializer'}
    )


class PeriodParticipantSerializer(ParticipantSerializer):
    class Meta(ParticipantSerializer.Meta):
        model = PeriodParticipant

        validators = [
            UniqueTogetherValidator(
                queryset=PeriodParticipant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/period-participants'

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{'document': 'bluebottle.time_based.serializers.PeriodParticipantDocumentSerializer'}
    )


class TimeContributionSerializer(BaseContributionSerializer):
    class Meta(BaseContributionSerializer.Meta):
        model = TimeContribution

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
