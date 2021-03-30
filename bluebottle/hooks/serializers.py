from rest_framework import serializers
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.utils.fields import FSMField

from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.time_based.models import PeriodActivity
from bluebottle.activities.models import Activity, Contributor


class DeedSerializer(ModelSerializer):
    status = FSMField(read_only=True)

    class Meta():
        model = Deed
        fields = ('status', 'title')

    class JSONAPIMeta:
        resource_name = 'activities/time-based/periods'


class PeriodActivitySerializer(ModelSerializer):
    status = FSMField(read_only=True)

    class Meta():
        model = PeriodActivity
        fields = ('status', 'title')

    class JSONAPIMeta:
        resource_name = 'activities/deeds'


class IncludedActivitySerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [DeedSerializer, PeriodActivitySerializer]

    class Meta():
        model = Activity
        fields = ('status', 'title')


class DeedParticipantSerializer(ModelSerializer):
    status = FSMField(read_only=True)

    class Meta():
        model = DeedParticipant
        fields = ('status', 'activity', 'user')

    class JSONAPIMeta:
        resource_name = 'contributors/deeds/participants'
        included_resources = [
            'user', 'activity',
        ]

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity': 'bluebottle.deeds.serializers.DeedSerializer',
    }


class IncludedContributorSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DeedParticipantSerializer
    ]

    class Meta:
        model = Contributor
        fields = ('status', 'activity', 'user')

    class JSONAPIMeta:
        included_resources = [
            'activity',
        ]

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity': 'bluebottle.deeds.serializers.DeedSerializer',
    }


class ContributorWebHookSerializer(serializers.Serializer):
    event = serializers.CharField()
    instance = IncludedContributorSerializer()

    class Meta:
        fields = ['event', 'instance']

    class JSONAPIMeta():
        resource_name = 'notification'
        included_resources = [
            'instance',
            'instance.activity',
            'instance.user',
        ]

    included_serializers = {
        'instance.user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'instance': IncludedContributorSerializer,
        'instance.activity': IncludedActivitySerializer,
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
