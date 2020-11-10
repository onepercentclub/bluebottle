from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import ResourceRelatedField

from rest_framework_json_api.serializers import PolymorphicModelSerializer
from rest_framework_json_api.relations import PolymorphicResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseActivityListSerializer,
    BaseContributionSerializer
)

from bluebottle.files.serializers import PrivateDocumentSerializer, PrivateDocumentField
from bluebottle.fsm.serializers import TransitionSerializer

from bluebottle.time_based.models import (
    TimeBasedActivity, OnADateActivity, WithADeadlineActivity,
    OnADateApplication, PeriodApplication
)
from bluebottle.time_based.permissions import ApplicationDocumentPermission
from bluebottle.time_based.filters import ApplicationListFilter

from bluebottle.utils.serializers import ResourcePermissionField, FilteredRelatedField
from bluebottle.utils.utils import reverse_signed


class TimeBasedBaseSerializer(BaseActivitySerializer):
    review = serializers.BooleanField(required=False)
    contributions = FilteredRelatedField(many=True, filter_backend=ApplicationListFilter)

    class Meta(BaseActivitySerializer.Meta):
        fields = BaseActivitySerializer.Meta.fields + (
            'capacity',
            'is_online',
            'location',
            'location_hint',
            'registration_deadline',
            'expertise',
            'review',
            'contributions'
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'location',
            'expertise',
            'contributions',
            'contributions.user',
            'contributions.document'
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'expertise': 'bluebottle.assignments.serializers.SkillSerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'contributions': 'bluebottle.time_based.serializers.ApplicationSerializer',
        }
    )


class OnADateActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('on-a-date-detail', view_args=('pk',))

    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        if instance.start and instance.duration:
            return {
                'ical': reverse_signed('on-a-date-ical', args=(instance.pk, )),
                'google': instance.google_calendar_link,
                'outlook': instance.outlook_link,
            }
        else:
            return {}

    class Meta(TimeBasedBaseSerializer.Meta):
        model = OnADateActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start', 'duration', 'links'
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/on-a-dates'

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'contributions': 'bluebottle.time_based.serializers.OnADateApplicationSerializer',
        }
    )


class WithADeadlineActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('with-a-deadline-detail', view_args=('pk',))

    class Meta(TimeBasedBaseSerializer.Meta):
        model = WithADeadlineActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start', 'deadline', 'duration', 'duration_period',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/with-a-deadlines'

    included_serializers = dict(
        TimeBasedBaseSerializer.included_serializers,
        **{
            'contributions': 'bluebottle.time_based.serializers.PeriodApplicationSerializer',
        }
    )


class TimeBasedActivitySerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        OnADateActivitySerializer,
        WithADeadlineActivitySerializer,
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


class OnADateTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=OnADateActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.OnADateActivitySerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/time-based/on-a-date-transitions'


class WithADeadlineTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=WithADeadlineActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.WithADeadlineActivitySerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/time-based/with-a-deadline-transitions'


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


class OnADateActivityListSerializer(TimeBasedActivityListSerializer):
    permissions = ResourcePermissionField('on-a-date-detail', view_args=('pk',))

    class Meta(TimeBasedActivityListSerializer.Meta):
        model = OnADateActivity
        fields = TimeBasedActivityListSerializer.Meta.fields + (
            'start', 'duration',
        )

    class JSONAPIMeta(TimeBasedActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/on-a-dates'


class WithADeadlineActivityListSerializer(TimeBasedActivityListSerializer):
    permissions = ResourcePermissionField('with-a-deadline-detail', view_args=('pk',))

    class Meta(TimeBasedActivityListSerializer.Meta):
        model = WithADeadlineActivity
        fields = TimeBasedActivityListSerializer.Meta.fields + (
            'deadline', 'duration', 'duration_period',
        )

    class JSONAPIMeta(TimeBasedActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/with-a-deadlines'


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
            'activity',
            'document'
        ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
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
            'resource.activity',
        ]


class OnADateApplicationTransitionSerializer(ApplicationTransitionSerializer):
    resource = ResourceRelatedField(queryset=OnADateApplication.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.OnADateApplicationSerializer',
        'resource.activity': 'bluebottle.activities.serializers.ActivitySerializer',
    }

    class JSONAPIMeta(ApplicationTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-based/on-a-date-application-transitions'


class PeriodApplicationTransitionSerializer(ApplicationTransitionSerializer):
    resource = ResourceRelatedField(queryset=PeriodApplication.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.PeriodApplicationSerializer',
        'resource.activity': 'bluebottle.activities.serializers.ActivitySerializer',
    }

    class JSONAPIMeta(ApplicationTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributions/time-based/period-application-transitions'
