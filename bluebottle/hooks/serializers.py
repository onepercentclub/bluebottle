from rest_framework import serializers
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.utils.fields import FSMField

from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.time_based.models import PeriodActivity
from bluebottle.activities.models import Activity, Contributor
from rest_framework_json_api.relations import PolymorphicResourceRelatedField


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


class IncludedActivitySerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [DeedSerializer, PeriodActivitySerializer]

    class Meta():
        model = Activity
        fields = ('status', 'title')

    class JSONAPIMeta:
        resource_name = 'activities'


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
        'activity': DeedSerializer
    }


class IncludedContributorSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DeedParticipantSerializer
    ]

    class Meta:
        model = Contributor
        fields = ('status', 'activity', 'user')

    class JSONAPIMeta:
        resource_name = 'contributors/deeds/participants'
        included_resources = [
            'activity',
            'user'
        ]

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity': IncludedActivitySerializer
    }


class ContributorWebHookSerializer(serializers.Serializer):
    event = serializers.CharField()
    instance = PolymorphicResourceRelatedField(
        polymorphic_serializer=IncludedContributorSerializer,
        read_only=True,
        model=Contributor
    )

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
    instance = PolymorphicResourceRelatedField(
        polymorphic_serializer=IncludedActivitySerializer,
        model=Activity,
        read_only=True
    )

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
