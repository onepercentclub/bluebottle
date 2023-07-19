from rest_framework import serializers

from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField
)

from bluebottle.updates.models import Update
from bluebottle.activities.serializers import ActivitySerializer
from bluebottle.activities.models import Activity


class UpdateSerializer(serializers.ModelSerializer):
    activity = PolymorphicResourceRelatedField(ActivitySerializer, queryset=Activity.objects.all())

    class Meta(object):
        model = Update

        fields = (
            'author',
            'activity',
            'message',
        )

    class JSONAPIMeta(object):
        resource_name = 'updates'

        included_resources = [
            'author',
        ]

    included_serializers = {
        'author': 'bluebottle.initiatives.serializers.MemberSerializer',
    }
