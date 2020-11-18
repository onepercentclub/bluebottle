from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import ResourceRelatedField

from rest_framework_json_api.serializers import PolymorphicModelSerializer
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField, SerializerMethodResourceRelatedField
)

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseActivityListSerializer,
    BaseContributionSerializer
)

from bluebottle.files.serializers import PrivateDocumentSerializer, PrivateDocumentField
from bluebottle.fsm.serializers import TransitionSerializer

from bluebottle.time_based.models import (
    TimeBasedActivity, DateActivity, PeriodActivity,
    OnADateApplication, PeriodApplication
)
from bluebottle.time_based.permissions import ApplicationDocumentPermission
from bluebottle.time_based.filters import ApplicationListFilter

from bluebottle.utils.serializers import ResourcePermissionField, FilteredRelatedField
from bluebottle.utils.utils import reverse_signed


class TimeBasedBaseSerializer(BaseActivitySerializer):
    review = serializers.BooleanField(required=False)

    class Meta(BaseActivitySerializer.Meta):
        fields = BaseActivitySerializer.Meta.fields + (
            'capacity',
            'is_online',
            'location',
            'location_hint',
            'registration_deadline',
            'expertise',
            'review',
            'contributions',
            'my_contribution'
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'location',
            'expertise',
            'my_contribution',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'expertise': 'bluebottle.assignments.serializers.SkillSerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class DateActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('date-detail', view_args=('pk',))
    my_contribution = SerializerMethodResourceRelatedField(
        model=OnADateApplication,
        read_only=True,
        source='get_my_contribution'
    )
    contributions = FilteredRelatedField(
        many=True,
        filter_backend=ApplicationListFilter,
        related_link_view_name='date-applications',

        related_link_url_kwarg='activity_id'
    )
    links = serializers.SerializerMethodField()

    def get_my_contribution(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.contributions.filter(user=user).instance_of(OnADateApplication).first()

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
            'start', 'duration', 'utc_offset', 'online_meeting_url', 'links'
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/dates'

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'my_contribution': 'bluebottle.time_based.serializers.OnADateApplicationSerializer'
        }
    )


class PeriodActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('period-detail', view_args=('pk',))

    my_contribution = SerializerMethodResourceRelatedField(
        model=OnADateApplication,
        read_only=True,
        source='get_my_contribution'
    )

    contributions = FilteredRelatedField(
        many=True,
        filter_backend=ApplicationListFilter,
        related_link_view_name='period-applications',
        related_link_url_kwarg='activity_id'

    )

    def get_my_contribution(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.contributions.filter(user=user).instance_of(OnADateApplication).first()

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
            'my_contribution': 'bluebottle.time_based.serializers.PeriodApplicationSerializer'
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


class ApplicationListSerializer(BaseContributionSerializer):
    activity = PolymorphicResourceRelatedField(
        TimeBasedActivitySerializer,
        queryset=TimeBasedActivity.objects.all()
    )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-based/applications'
        included_resources = [
            'user',
            'activity',
        ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.TinyActivitySerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class OnADateApplicationListSerializer(ApplicationListSerializer):
    class Meta(ApplicationListSerializer.Meta):
        model = OnADateApplication

    class JSONAPIMeta(ApplicationListSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-based/on-a-date-applications'


class PeriodApplicationListSerializer(ApplicationListSerializer):
    class Meta(ApplicationListSerializer.Meta):
        model = PeriodApplication

    class JSONAPIMeta(ApplicationListSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-based/period-applications'


class ApplicationSerializer(BaseContributionSerializer):
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

    class Meta(BaseContributionSerializer.Meta):
        model = OnADateApplication
        fields = BaseContributionSerializer.Meta.fields + (
            'motivation',
            'document'
        )

        validators = [
            UniqueTogetherValidator(
                queryset=OnADateApplication.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-based/applications'
        included_resources = [
            'user',
            'document'
        ]

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class OnADateApplicationSerializer(ApplicationSerializer):
    class Meta(ApplicationSerializer.Meta):
        model = OnADateApplication

        validators = [
            UniqueTogetherValidator(
                queryset=OnADateApplication.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(ApplicationSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-based/on-a-date-applications'

    included_serializers = dict(
        ApplicationSerializer.included_serializers,
        **{'document': 'bluebottle.time_based.serializers.OnADateApplicationDocumentSerializer'}
    )


class PeriodApplicationSerializer(ApplicationSerializer):
    class Meta(ApplicationSerializer.Meta):
        model = PeriodApplication

        validators = [
            UniqueTogetherValidator(
                queryset=PeriodApplication.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(ApplicationSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-based/period-applications'

    included_serializers = dict(
        ApplicationSerializer.included_serializers,
        **{'document': 'bluebottle.time_based.serializers.PeriodApplicationDocumentSerializer'}
    )


class ApplicationTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=OnADateApplication.objects.all())
    field = 'states'

    class JSONAPIMeta(object):
        resource_name = 'contributions/time-based/application-transitions'
        included_resources = [
            'resource',
        ]


class OnADateApplicationTransitionSerializer(ApplicationTransitionSerializer):
    resource = ResourceRelatedField(queryset=OnADateApplication.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.OnADateApplicationSerializer',
    }

    class JSONAPIMeta(ApplicationTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-based/on-a-date-application-transitions'


class PeriodApplicationTransitionSerializer(ApplicationTransitionSerializer):
    resource = ResourceRelatedField(queryset=PeriodApplication.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.PeriodApplicationSerializer',
    }

    class JSONAPIMeta(ApplicationTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-based/period-application-transitions'
