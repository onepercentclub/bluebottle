from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import ResourceRelatedField

from rest_framework_json_api.serializers import PolymorphicModelSerializer
from rest_framework_json_api.relations import PolymorphicResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseActivityListSerializer,
    BaseContributorSerializer
)

from bluebottle.files.serializers import PrivateDocumentSerializer, PrivateDocumentField
from bluebottle.fsm.serializers import TransitionSerializer

from bluebottle.time_based.models import (
    TimeBasedActivity, DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant
)
from bluebottle.time_based.permissions import ApplicationDocumentPermission
from bluebottle.time_based.filters import ApplicationListFilter

from bluebottle.utils.serializers import ResourcePermissionField, FilteredRelatedField
from bluebottle.utils.utils import reverse_signed


class TimeBasedBaseSerializer(BaseActivitySerializer):
    review = serializers.BooleanField(required=False)
    contributors = FilteredRelatedField(many=True, filter_backend=ApplicationListFilter)

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
            'contributors',
            'contributors.user',
            'contributors.document'
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'expertise': 'bluebottle.assignments.serializers.SkillSerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'contributors': 'bluebottle.time_based.serializers.ApplicationSerializer',
        }
    )


class DateActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('date-detail', view_args=('pk',))

    links = serializers.SerializerMethodField()

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
            'start', 'duration', 'online_meeting_url', 'links'
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/dates'

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'contributors': 'bluebottle.time_based.serializers.OnADateApplicationSerializer',
        }
    )


class PeriodActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('period-detail', view_args=('pk',))

    class Meta(TimeBasedBaseSerializer.Meta):
        model = PeriodActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start', 'deadline', 'duration', 'duration_period',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/periods'

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'contributors': 'bluebottle.time_based.serializers.PeriodApplicationSerializer',
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


class OnADateApplicationDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'period-application-document'
    relationship = 'onadateapplication_set'


class PeriodApplicationDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'on-a-date-application-document'
    relationship = 'periodapplication_set'


class ApplicationListSerializer(BaseContributorSerializer):
    activity = PolymorphicResourceRelatedField(
        TimeBasedActivitySerializer,
        queryset=TimeBasedActivity.objects.all()
    )

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/applications'
        included_resources = [
            'user',
            'activity',
        ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.TinyActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class OnADateApplicationListSerializer(ApplicationListSerializer):
    class Meta(ApplicationListSerializer.Meta):
        model = DateParticipant

    class JSONAPIMeta(ApplicationListSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-applications'


class PeriodApplicationListSerializer(ApplicationListSerializer):
    class Meta(ApplicationListSerializer.Meta):
        model = PeriodParticipant

    class JSONAPIMeta(ApplicationListSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/period-applications'


class ApplicationSerializer(BaseContributorSerializer):
    motivation = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    document = PrivateDocumentField(required=False, allow_null=True, permissions=[ApplicationDocumentPermission])

    activity = PolymorphicResourceRelatedField(
        TimeBasedActivitySerializer,
        queryset=TimeBasedActivity.objects.all()
    )

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
            'document'
        )

        validators = [
            UniqueTogetherValidator(
                queryset=DateParticipant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/applications'
        included_resources = [
            'user',
            'activity',
            'document'
        ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class OnADateApplicationSerializer(ApplicationSerializer):
    class Meta(ApplicationSerializer.Meta):
        model = DateParticipant

        validators = [
            UniqueTogetherValidator(
                queryset=DateParticipant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(ApplicationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-applications'

    included_serializers = dict(
        ApplicationSerializer.included_serializers,
        **{'document': 'bluebottle.time_based.serializers.OnADateApplicationDocumentSerializer'}
    )


class PeriodApplicationSerializer(ApplicationSerializer):
    class Meta(ApplicationSerializer.Meta):
        model = PeriodParticipant

        validators = [
            UniqueTogetherValidator(
                queryset=PeriodParticipant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(ApplicationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/period-applications'

    included_serializers = dict(
        ApplicationSerializer.included_serializers,
        **{'document': 'bluebottle.time_based.serializers.PeriodApplicationDocumentSerializer'}
    )


class ApplicationTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DateParticipant.objects.all())
    field = 'states'

    class JSONAPIMeta(object):
        resource_name = 'contributors/time-based/application-transitions'
        included_resources = [
            'resource',
            'resource.activity',
        ]


class OnADateApplicationTransitionSerializer(ApplicationTransitionSerializer):
    resource = ResourceRelatedField(queryset=DateParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.OnADateApplicationSerializer',
        'resource.activity': 'bluebottle.activities.serializers.ActivitySerializer',
    }

    class JSONAPIMeta(ApplicationTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-application-transitions'


class PeriodApplicationTransitionSerializer(ApplicationTransitionSerializer):
    resource = ResourceRelatedField(queryset=PeriodParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.PeriodApplicationSerializer',
        'resource.activity': 'bluebottle.activities.serializers.ActivitySerializer',
    }

    class JSONAPIMeta(ApplicationTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/period-application-transitions'
