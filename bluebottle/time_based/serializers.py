from rest_framework import serializers

from bluebottle.activities.utils import (
    BaseActivitySerializer,
)
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
        resource_name = 'activities/time-based/on-a-date'


class WithADeadlineActivitySerializer(TimeBasedSerializer):
    class Meta(TimeBasedSerializer.Meta):
        model = WithADeadlineActivity
        fields = TimeBasedSerializer.Meta.fields + (
            'deadline', 'duration', 'duration_type',
        )

    class JSONAPIMeta(TimeBasedSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/with-a-deadline'


class OngoingActivitySerializer(TimeBasedSerializer):
    class Meta(TimeBasedSerializer.Meta):
        model = OngoingActivity

        fields = TimeBasedSerializer.Meta.fields + (
            'duration', 'duration_type',
        )

    class JSONAPIMeta(TimeBasedSerializer.JSONAPIMeta):
        resource_name = 'activities/time-based/ongoing'
