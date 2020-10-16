from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseActivityListSerializer
)

from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.utils.serializers import NoCommitMixin
from bluebottle.time_based.models import OnADateActivity, WithADeadlineActivity, OngoingActivity


class TimeBasedSerializer(NoCommitMixin, BaseActivitySerializer):
    is_online = serializers.BooleanField(required=False)
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
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'location',
            'expertise',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'expertise': 'bluebottle.assignments.serializers.SkillSerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class OnADateActivitySerializer(TimeBasedSerializer):
    class Meta(TimeBasedSerializer.Meta):
        model = OnADateActivity
        fields = TimeBasedSerializer.Meta.fields + (
            'start', 'duration',
        )

    class JSONAPIMeta(TimeBasedSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/on-a-dates'


class WithADeadlineActivitySerializer(TimeBasedSerializer):
    class Meta(TimeBasedSerializer.Meta):
        model = WithADeadlineActivity
        fields = TimeBasedSerializer.Meta.fields + (
            'deadline', 'duration', 'duration_period',
        )

    class JSONAPIMeta(TimeBasedSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/with-a-deadlines'


class OngoingActivitySerializer(TimeBasedSerializer):
    class Meta(TimeBasedSerializer.Meta):
        model = OngoingActivity

        fields = TimeBasedSerializer.Meta.fields + (
            'duration', 'duration_period',
        )

    class JSONAPIMeta(TimeBasedSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/ongoings'


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
    class Meta(TimeBasedActivityListSerializer.Meta):
        model = OnADateActivity
        fields = TimeBasedActivityListSerializer.Meta.fields + (
            'start', 'duration',
        )

    class JSONAPIMeta(TimeBasedActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/on-a-dates'


class WithADeadlineActivityListSerializer(TimeBasedActivityListSerializer):
    class Meta(TimeBasedActivityListSerializer.Meta):
        model = WithADeadlineActivity
        fields = TimeBasedActivityListSerializer.Meta.fields + (
            'deadline', 'duration', 'duration_period',
        )

    class JSONAPIMeta(TimeBasedActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/with-a-deadlines'


class OngoingActivityListSerializer(TimeBasedActivityListSerializer):
    class Meta(TimeBasedActivityListSerializer.Meta):
        model = OngoingActivity

        fields = TimeBasedActivityListSerializer.Meta.fields + (
            'duration', 'duration_period',
        )

    class JSONAPIMeta(TimeBasedActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/ongoings'
