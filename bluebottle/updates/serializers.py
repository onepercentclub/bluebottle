from rest_framework import serializers

from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField, ResourceRelatedField
)

from bluebottle.updates.models import Update
from bluebottle.activities.serializers import ActivitySerializer
from bluebottle.activities.models import Activity
from bluebottle.files.serializers import ImageSerializer, ImageField


def no_nested_replies_validator(value):
    if value and value.parent:
        raise serializers.ValidationError('Replies cannot be nested')


class UpdateSerializer(serializers.ModelSerializer):
    activity = PolymorphicResourceRelatedField(ActivitySerializer, queryset=Activity.objects.all())
    image = ImageField(required=False, allow_null=True)
    parent = ResourceRelatedField(
        queryset=Update.objects.all(),
        validators=[no_nested_replies_validator],
        required=False
    )
    replies = ResourceRelatedField(many=True, read_only=True)

    class Meta(object):
        model = Update

        fields = (
            'message',
            'created',
            'image',
            'author',
            'activity',
            'parent',
            'replies'
        )

    class JSONAPIMeta(object):
        resource_name = 'updates'

        included_resources = [
            'author', 'image', 'replies'
        ]

    included_serializers = {
        'author': 'bluebottle.initiatives.serializers.MemberSerializer',
        'image': 'bluebottle.updates.serializers.UpdateImageSerializer',
        'replies': 'bluebottle.updates.serializers.UpdateSerializer',
    }


IMAGE_SIZES = {
    'large': '600x337',
}


class UpdateImageSerializer(ImageSerializer):
    sizes = IMAGE_SIZES
    content_view_name = 'update-image'
    relationship = 'update_set'
