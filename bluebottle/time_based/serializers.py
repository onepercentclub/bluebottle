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
from bluebottle.utils.serializers import ResourcePermissionField, FilteredRelatedField

from bluebottle.time_based.models import (
    TimeBasedActivity, OnADateActivity, WithADeadlineActivity, OngoingActivity, Application
)
from bluebottle.time_based.permissions import ApplicationDocumentPermission
from bluebottle.time_based.filters import ApplicationListFilter


class TimeBasedBaseSerializer(BaseActivitySerializer):
    is_online = serializers.BooleanField(required=False)
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

    class Meta(TimeBasedBaseSerializer.Meta):
        model = OnADateActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'start', 'duration',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/on-a-dates'


class WithADeadlineActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('with-a-deadline-detail', view_args=('pk',))

    class Meta(TimeBasedBaseSerializer.Meta):
        model = WithADeadlineActivity
        fields = TimeBasedBaseSerializer.Meta.fields + (
            'deadline', 'duration', 'duration_period',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/with-a-deadlines'


class OngoingActivitySerializer(TimeBasedBaseSerializer):
    permissions = ResourcePermissionField('ongoing-detail', view_args=('pk',))

    class Meta(TimeBasedBaseSerializer.Meta):
        model = OngoingActivity

        fields = TimeBasedBaseSerializer.Meta.fields + (
            'duration', 'duration_period',
        )

    class JSONAPIMeta(TimeBasedBaseSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/ongoings'


class TimeBasedActivitySerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        OnADateActivitySerializer,
        WithADeadlineActivitySerializer,
        OngoingActivitySerializer,
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


class OngoingTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=OngoingActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.OngoingActivitySerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/time-based/ongoing-transitions'


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


class OngoingActivityListSerializer(TimeBasedActivityListSerializer):
    permissions = ResourcePermissionField('ongoing-detail', view_args=('pk',))

    class Meta(TimeBasedActivityListSerializer.Meta):
        model = OngoingActivity

        fields = TimeBasedActivityListSerializer.Meta.fields + (
            'duration', 'duration_period',
        )

    class JSONAPIMeta(TimeBasedActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/ongoings'


class ApplicationDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'application-document'
    relationship = 'application_set'


class ApplicationListSerializer(BaseContributionSerializer):
    activity = PolymorphicResourceRelatedField(
        TimeBasedActivitySerializer,
        queryset=TimeBasedActivity.objects.all()
    )

    class Meta(BaseContributionSerializer.Meta):
        model = Application

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
        model = Application
        fields = BaseContributionSerializer.Meta.fields + (
            'motivation',
            'document'
        )

        validators = [
            UniqueTogetherValidator(
                queryset=Application.objects.all(),
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
        'document': 'bluebottle.time_based.serializers.ApplicationDocumentSerializer',
    }


class ApplicationTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Application.objects.all())
    field = 'states'
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.ApplicationSerializer',
        'resource.activity': 'bluebottle.activities.serializers.ActivitySerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'contributions/time-based/application-transitions'
        included_resources = [
            'resource',
            'resource.activity',
        ]
