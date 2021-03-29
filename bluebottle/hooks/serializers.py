from rest_framework import serializers
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.utils.fields import FSMField

from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.activities.models import Activity, Contributor


class DeedSerializer(ModelSerializer):
    status = FSMField(read_only=True)

    class Meta():
        model = Deed
        fields = ('status', 'title')

    class JSONAPIMeta:
        resource_name = 'activities/deeds'


class IncludedActivitySerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [DeedSerializer]

    class Meta():
        model = Activity
        fields = ('status', 'title')


class DeedParticipantSerializer(ModelSerializer):
    status = FSMField(read_only=True)

    class Meta():
        model = DeedParticipant
        fields = ('status', 'activity')

    class JSONAPIMeta:
        resource_name = 'contributors'


class IncludedContributorSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [DeedParticipantSerializer]

    class Meta:
        model = Contributor
        fields = ('status', 'activity')

    class JSONAPIMeta:
        included_resources = [
            'activity',
        ]

    @property
    def included_serializers(self):
        return {'activity': IncludedActivitySerializer}


class ContributorWebHookSerializer(serializers.Serializer):
    event = serializers.CharField()
    instance = IncludedContributorSerializer()

    class Meta:
        fields = ['event', 'instance']

    class JSONAPIMeta():
        resource_name = 'notification'
        included_resources = [
            'instance', 'instance.activity'
        ]

    included_serializers = {
        'instance': IncludedContributorSerializer,
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
