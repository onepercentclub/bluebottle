from rest_framework import serializers

from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField
)

from bluebottle.updates.models import Update
from bluebottle.activities.serializers import ActivitySerializer
from bluebottle.activities.models import Activity
from bluebottle.files.serializers import ImageSerializer, ImageField


class UpdateSerializer(serializers.ModelSerializer):
    activity = PolymorphicResourceRelatedField(ActivitySerializer, queryset=Activity.objects.all())
    image = ImageField(required=False, allow_null=True)

    class Meta(object):
        model = Update

        fields = (
            'author',
            'activity',
            'message',
            'image',
        )

    class JSONAPIMeta(object):
        resource_name = 'updates'

        included_resources = [
            'author', 'image'
        ]

    included_serializers = {
        'author': 'bluebottle.initiatives.serializers.MemberSerializer',
        'image': 'bluebottle.updates.serializers.UpdateImageSerializer',
    }


IMAGE_SIZES = {
    'large': '600x337',
}


class UpdateImageSerializer(ImageSerializer):
    sizes = IMAGE_SIZES
    content_view_name = 'update-image'
    relationship = 'update_set'
