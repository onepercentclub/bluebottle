from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField, SerializerMethodResourceRelatedField, ResourceRelatedField,
    HyperlinkedRelatedField, SerializerMethodHyperlinkedRelatedField

)
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

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
    TimeBasedActivity, DateActivity,
    DateParticipant, TimeContribution, DateActivitySlot,
    DateRegistration, Skill
)
from bluebottle.time_based.permissions import ParticipantDocumentPermission, CanExportParticipantsPermission
from bluebottle.time_based.serializers import RegistrationTransitionSerializer, RegistrationSerializer, \
    DateActivitySerializer
from bluebottle.utils.fields import ValidationErrorsField, RequiredErrorsField, FSMField
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.utils.utils import reverse_signed


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
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'expertise',
            'my_contributor',
            'my_contributor.user',
            'my_contributor.contributions',
            'my_contributor.document',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'expertise': 'bluebottle.time_based.serializers.SkillSerializer',
            'my_contributor.contributions': 'bluebottle.time_based.serializers.TimeContributionSerializer',
            'my_contributor.user': 'bluebottle.initiatives.serializers.MemberSerializer',
        }
    )


class ActivitySlotSerializer(ModelSerializer):
    is_online = serializers.BooleanField(required=False, allow_null=True)
    permissions = ResourcePermissionField('date-slot-detail', view_args=('pk',))
    transitions = AvailableTransitionsField(source='states')
    status = FSMField(read_only=True)
    location = ResourceRelatedField(queryset=Geolocation.objects, required=False, allow_null=True)
    current_status = CurrentStatusField(source='states.current_state')
    timezone = serializers.SerializerMethodField()

    my_contributor = SerializerMethodResourceRelatedField(
        model=DateParticipant,
        read_only=True,
    )

    participants_export_url = PrivateFileSerializer(
        'date-participant-export',
        url_args=('pk',),
        filename='participant.csv',
        permission=CanExportParticipantsPermission,
        read_only=True
    )

    def get_timezone(self, instance):
        is_online = getattr(instance, 'is_online', False)
        has_location = getattr(instance, 'location', False)
        return instance.location.timezone if not is_online and has_location else None

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.participants.filter(user=user).first()

    class Meta:
        fields = (
            'id',
            'activity',
            'start',
            'end',
            'transitions',
            'is_online',
            'timezone',
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
        related_link_view_name='date-participants',
        related_link_url_kwarg='slot_id',
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
                        participants__status__in=['registered', 'succeeded'],
                        participants__participant_id=contributor_id
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
        included_resources = [
            'activity',
            'my_contributor',
            'my_contributor.user',
            'location',
            'location.country'
        ]

    included_serializers = dict(
        ActivitySlotSerializer.included_serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'country': 'bluebottle.geo.serializers.CountrySerializer',
            'my_contributor': 'bluebottle.time_based.serializers.DateParticipantSerializer',
            'my_contributor.user': 'bluebottle.initiatives.serializers.MemberSerializer',
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


class TimeBasedActivitySerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DateActivitySerializer,
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


class DateParticipantDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'date-participant-document'
    relationship = 'dateparticipant_set'


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


class ParticipantSerializer(BaseContributorSerializer):
    total_duration = serializers.DurationField(read_only=True)
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
            'total_duration'
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


class DateRegistrationParticipantSerializer(RegistrationSerializer):
    slot_count = serializers.SerializerMethodField()

    participants = HyperlinkedRelatedField(
        many=True,
        read_only=True,
        related_link_view_name='related-participant-list',
        related_link_url_kwarg='participant_id',
    )

    permissions = ResourcePermissionField('date-participant-detail', view_args=('pk',))

    def get_slot_count(self, obj):
        return obj.participants.count()

    class Meta(ParticipantSerializer.Meta):
        model = DateParticipant
        meta_fields = RegistrationSerializer.Meta.meta_fields + ('permissions', 'slot_count')
        fields = RegistrationSerializer.Meta.fields + ['participants', ]
        validators = [
            UniqueTogetherValidator(
                queryset=DateRegistration.objects.all(),
                fields=('activity', 'user',)
            )
        ]

    class JSONAPIMeta(RegistrationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-registrations'
        included_resources = RegistrationSerializer.JSONAPIMeta.included_resources + [
            'activity',
        ]

    included_serializers = dict(
        RegistrationSerializer.included_serializers,
        **{
            'user': 'bluebottle.initiatives.serializers.MemberSerializer',
            'document': 'bluebottle.time_based.serializers.DateParticipantDocumentSerializer',
            'activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
        }
    )


def activity_matches_participant_and_slot(value):
    if value['slot'].activity != value['participant'].activity:
        raise serializers.ValidationError(
            'The activity of the slot does not match the activity of the participant.'
        )


class DateParticipantSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    transitions = AvailableTransitionsField(source='states')
    current_status = CurrentStatusField(source='states.current_state')
    permissions = ResourcePermissionField('date-participant-detail', view_args=('pk',))
    email = serializers.EmailField(write_only=True, required=False)
    send_messages = serializers.BooleanField(write_only=True, required=False)
    user = ResourceRelatedField(
        read_only=True,
        model=BlueBottleBaseUser,
        default=serializers.CurrentUserDefault()
    )
    slot = ResourceRelatedField(queryset=DateActivitySlot.objects)

    def validate(self, data):
        email = data.get('email', None)
        if data['slot'].status != 'open' and not email:
            raise ValidationError('Participants cannot sign up for full slots')
        return data

    class Meta:
        model = DateParticipant
        fields = [
            'id',
            'registration',
            'current_status',
            'user',
            'slot',
            'email',
            'send_messages'
        ]
        meta_fields = ('status', 'transitions', 'current_status', 'permissions')

        validators = []

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-participants'
        included_resources = [
            'registration',
            'user',
            'slot',
            'slot.activity',
        ]

    included_serializers = {
        'registration': 'bluebottle.time_based.serializers.DateRegistrationSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'slot': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
        'slot.activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
    }


class DateParticipantTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DateParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.SlotParticipantSerializer',
        'resource.registration': 'bluebottle.time_based.serializers.DateRegistrationSerializer',
        'resource.slot': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', 'resource.slot', 'resource.participant']
        resource_name = 'contributors/time-based/date-participant-transitions'


class TimeContributionSerializer(BaseContributionSerializer):
    permissions = ResourcePermissionField('time-contribution-detail', view_args=('pk',))

    class Meta(BaseContributionSerializer.Meta):
        model = TimeContribution
        fields = BaseContributionSerializer.Meta.fields + ("contribution_type", "start")
        meta_fields = BaseContributionSerializer.Meta.meta_fields + ("permissions",)

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


class DateRegistrationTransitionSerializer(RegistrationTransitionSerializer):
    resource = ResourceRelatedField(queryset=DateParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DateRegistrationSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
    }

    class JSONAPIMeta(ParticipantTransitionSerializer.JSONAPIMeta):
        included_resources = [
            'resource',
            'resource.activity'
        ]
        resource_name = 'contributors/time-based/date-registration-transitions'


class SkillSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta(object):
        model = Skill
        fields = ('id', 'name', 'expertise')

    class JSONAPIMeta(object):
        included_resources = ['resource']
        resource_name = 'skills'
