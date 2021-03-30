from rest_framework import serializers
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.activities.models import Activity, Contributor
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.time_based.models import PeriodActivity
from bluebottle.utils.fields import FSMField


class DeedSerializer(ModelSerializer):
    status = FSMField(read_only=True)

    class Meta():
        model = Deed
        fields = ('status', 'title')

    class JSONAPIMeta:
        resource_name = 'activities/deeds'


class PeriodActivitySerializer(ModelSerializer):
    status = FSMField(read_only=True)

    class Meta():
        model = PeriodActivity
        fields = ('status', 'title')

    class JSONAPIMeta:
        resource_name = 'activities/time-based/periods'


class DateActivitySerializer(ModelSerializer):
    status = FSMField(read_only=True)

    class Meta():
        model = PeriodActivity
        fields = ('status', 'title')

    class JSONAPIMeta:
        resource_name = 'activities/time-based/dates'


class DeedParticipantSerializer(ModelSerializer):
    status = FSMField(read_only=True)

    class Meta():
        model = DeedParticipant
        fields = ('id', 'status',)

    class JSONAPIMeta:
        resource_name = 'contributors/deeds/participants'
        included_resources = [
            'activity'
            'user'
        ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class IncludedActivitySerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DeedSerializer,
        PeriodActivitySerializer,
    ]

    class Meta():
        model = Activity
        fields = ('id', 'status', 'title')


class IncludedContributorSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [DeedParticipantSerializer]

    class Meta:
        model = Contributor
        fields = ('id', 'status', 'activity', 'user')

    class JSONAPIMeta:
        included_resources = [
            'activity',
            'user'
        ]
        resource_name = 'contributors/deeds/participant'

    included_serializers = {
        'activity': 'bluebottle.hooks.serializers.IncludedActivitySerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class ContributorWebHookSerializer(serializers.Serializer):
    event = serializers.CharField()
    created = serializers.DateTimeField()
    instance = IncludedContributorSerializer()

    class Meta:
        fields = ['event', 'created', 'instance']

    class JSONAPIMeta():
        resource_name = 'notification'
        included_resources = [
            'instance.activity'
            'instance.user'
        ]

    included_serializers = {
        'instance': IncludedContributorSerializer,
        'instance.activity': IncludedActivitySerializer,
        'instance.user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class ActivityWebHookSerializer(serializers.Serializer):
    event = serializers.CharField()
    instance = IncludedActivitySerializer()

    class Meta:
        fields = ['event', 'instance']

    class JSONAPIMeta():
        resource_name = 'notification'
        included_resources = [
            'instance',
        ]

    included_serializers = {
        'instance': IncludedActivitySerializer,
    }
