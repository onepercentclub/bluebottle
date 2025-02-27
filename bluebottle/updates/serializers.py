import hashlib
import os

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_tools.middlewares.ThreadLocal import get_current_user
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField, ResourceRelatedField
)
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivitySerializer, ContributorSerializer
from bluebottle.files.models import Image
from bluebottle.files.serializers import ImageSerializer
from bluebottle.funding.models import FundingPlatformSettings
from bluebottle.updates.models import Update, UpdateImage
from bluebottle.utils.serializers import ResourcePermissionField


def no_nested_replies_validator(value):
    if value and value.parent:
        raise serializers.ValidationError('Replies cannot be nested')


class UpdateSerializer(ModelSerializer):
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
        required=False,
        allow_null=True
    )
    replies = ResourceRelatedField(many=True, read_only=True)
    author = ResourceRelatedField(
        read_only=True
    )
    contribution = PolymorphicResourceRelatedField(
        read_only=True,
        polymorphic_serializer=ContributorSerializer
    )

    permissions = ResourcePermissionField('update-detail', view_args=('pk',))

    def to_representation(self, instance):
        data = super().to_representation(instance)
        anonymous = FundingPlatformSettings.load().anonymous_donations
        current_user = get_current_user()
        if instance.contribution and anonymous and data['author'] != current_user:
            data['author'] = None
        if instance.fake_name:
            data['author'] = None
        if instance.contribution and instance.contribution.anonymous:
            data['author'] = None

        return data

    def validate(self, value):
        if self.partial:
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
            'permissions',
            'contribution',
            'fake_name',
        )
        meta_fields = (
            'permissions',
        )

    class JSONAPIMeta(object):
        resource_name = 'updates'

        included_resources = [
            'author',
            'author.avatar',
            'image',
            'replies',
            'images',
            'contribution',
            'activity'
        ]

    included_serializers = {
        'author.avatar': 'bluebottle.initiatives.serializers.AvatarImageSerializer',
        'author': 'bluebottle.initiatives.serializers.MemberSerializer',
        'images': 'bluebottle.updates.serializers.UpdateImageSerializer',
        'replies': 'bluebottle.updates.serializers.UpdateSerializer',
        'contribution': 'bluebottle.activities.serializers.ContributorSerializer',
        'activity': 'bluebottle.activities.serializers.ActivitySerializer',
    }


IMAGE_SIZES = {
    'small': '150x150',
    'medium': '800x450',
    'large': '1600x900',
}


class UpdateImageListSerializer(ModelSerializer):
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
