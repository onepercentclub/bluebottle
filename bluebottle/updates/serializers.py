import hashlib
import os

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField, ResourceRelatedField
)

from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivitySerializer
from bluebottle.files.models import Image
from bluebottle.files.serializers import ImageSerializer
from bluebottle.updates.models import Update, UpdateImage
from bluebottle.utils.serializers import ResourcePermissionField


def no_nested_replies_validator(value):
    if value and value.parent:
        raise serializers.ValidationError('Replies cannot be nested')


class UpdateSerializer(serializers.ModelSerializer):
    activity = PolymorphicResourceRelatedField(
        ActivitySerializer,
        queryset=Activity.objects.all(),
        required=False
    )
    images = ResourceRelatedField(
        many=True,
        read_only=True
    )
    parent = ResourceRelatedField(
        queryset=Update.objects.all(),
        validators=[no_nested_replies_validator],
        required=False
    )
    replies = ResourceRelatedField(many=True, read_only=True)

    permissions = ResourcePermissionField('update-detail', view_args=('pk',))

    def validate(self, value):
        return value
        image_count = self.context['request'].data.get('images', [])
        if not (value.get('message') or value.get('video_url') or image_count):
            raise ValidationError(
                _("At least one of 'message', 'images', or 'video_url' must be set.")
            )
        return value

    class Meta(object):
        model = Update

        fields = (
            'message',
            'created',
            'images',
            'author',
            'activity',
            'parent',
            'replies',
            'notify',
            'video_url',
            'pinned',
            'permissions'
        )
        meta_fields = (
            'permissions',
        )

    class JSONAPIMeta(object):
        resource_name = 'updates'

        included_resources = [
            'author', 'image', 'replies', 'images'
        ]

    included_serializers = {
        'author': 'bluebottle.initiatives.serializers.MemberSerializer',
        'images': 'bluebottle.updates.serializers.UpdateImageSerializer',
        'replies': 'bluebottle.updates.serializers.UpdateSerializer',
    }


IMAGE_SIZES = {
    'small': '150x150',
    'large': '600x600',
}


class UpdateImageListSerializer(serializers.ModelSerializer):
    image = ResourceRelatedField(queryset=Image.objects.all())
    update = ResourceRelatedField(queryset=Update.objects.all())

    class JSONAPIMeta(object):
        resource_name = 'updates/images'

    class Meta(object):
        model = UpdateImage
        fields = ('id', 'update', 'image')
        meta_fields = ['filename']


class UpdateImageSerializer(ImageSerializer):
    sizes = IMAGE_SIZES
    content_view_name = 'update-image'
    relationship = 'update'

    class JSONAPIMeta(object):
        resource_name = 'updates/images'

    def get_links(self, obj):
        if hasattr(self, 'sizes'):
            parent = getattr(obj, self.relationship)
            if parent:
                hash = hashlib.md5(obj.image.file.name.encode('utf-8')).hexdigest()
                return dict(
                    (
                        key,
                        reverse(self.content_view_name, args=(obj.pk, size, )) + '?_={}'.format(hash)
                    ) for key, size in list(self.sizes.items())
                )

    def get_filename(self, instance):
        return os.path.basename(instance.image.file.name)
