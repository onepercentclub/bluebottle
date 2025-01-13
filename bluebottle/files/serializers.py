import hashlib
import os
from builtins import object

from django.db.models import QuerySet
from django.urls import reverse
from django.core.files.images import ImageFile
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.files.models import Document, Image, PrivateDocument
from bluebottle.utils.utils import reverse_signed


class DocumentField(ResourceRelatedField):
    model = Document


class PrivateDocumentField(DocumentField):
    """
    Only users with right permissions can view these documents.
    """
    queryset = PrivateDocument.objects
    permissions = []
    model = PrivateDocument

    def __init__(self, permissions, **kwargs):
        self.permissions = permissions
        super(PrivateDocumentField, self).__init__(**kwargs)

    def has_parent_permissions(self, parent):
        request = self.context['request']
        for permission in self.permissions:
            if not permission().has_object_permission(request, None, parent):
                return False
        return True

    def get_queryset(self):
        queryset = super(PrivateDocumentField, self).get_queryset()
        parent = self.parent.instance
        if not self.has_parent_permissions(parent):
            return queryset.none()
        return queryset

    def to_representation(self, value):
        parent = self.parent.instance
        # We might have a list when getting this for included serializers
        if isinstance(parent, (QuerySet, tuple, list)):
            parent = self.context['view'].get_queryset().filter(**{self.field_name: value.pk}).first()

        if not self.has_parent_permissions(parent):
            return None

        return super(PrivateDocumentField, self).to_representation(value)


class FileSerializer(ModelSerializer):
    file = serializers.FileField(write_only=True)
    filename = serializers.SerializerMethodField()
    owner = ResourceRelatedField(read_only=True)

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(object):
        model = Document
        fields = ('id', 'file', 'filename', 'owner',)
        meta_fields = ['filename']

    class JSONAPIMeta(object):
        included_resources = ['owner', ]

    def get_filename(self, instance):
        return os.path.basename(instance.file.name)


class PrivateFileSerializer(FileSerializer):
    class Meta(object):
        model = PrivateDocument
        fields = ('id', 'file', 'filename', 'owner',)
        meta_fields = ['filename']


class DocumentSerializer(ModelSerializer):
    file = serializers.FileField(write_only=True)
    filename = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    owner = ResourceRelatedField(read_only=True)

    relationship = None
    content_view_name = None

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    def get_link(self, obj):
        if self.relationship and self.content_view_name:
            parent = getattr(obj, self.relationship).first()

            if parent:
                return reverse(self.content_view_name, args=(parent.pk, 'main'))

    def get_filename(self, instance):
        return instance.name or os.path.basename(instance.file.name)

    class Meta(object):
        model = Document
        fields = ('id', 'file', 'filename', 'owner', 'link',)
        meta_fields = ['filename']

    class JSONAPIMeta(object):
        included_resources = ['owner', ]


class PrivateDocumentSerializer(DocumentSerializer):
    def get_link(self, obj):
        if self.relationship:
            parent = getattr(obj, self.relationship).first()
            if parent:
                return reverse_signed(self.content_view_name, args=(parent.pk,))

    class Meta(object):
        model = PrivateDocument
        fields = ('id', 'file', 'filename', 'owner', 'link',)
        meta_fields = ['filename']


class ImageField(ResourceRelatedField):
    queryset = Image.objects


ORIGINAL_SIZE = '1500'
IMAGE_SIZES = {
    "email": "200x200",
    "avatar": "200x200",
    "preview": "292x164",
    "small": "320x180",
    "large": "600x337",
    "cover": "1568x882",
}


class ImageSerializer(DocumentSerializer):
    links = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()

    sizes = IMAGE_SIZES

    def get_size(self, obj):
        try:
            obj.file.seek(0)
            image_file = ImageFile(obj.file)

            return {'width': image_file.width, 'height': image_file.height}
        except FileNotFoundError:
            pass

    def get_links(self, obj):
        hash = hashlib.md5(obj.file.name.encode('utf-8')).hexdigest()
        sizes = dict(original=ORIGINAL_SIZE, **self.sizes)
        if self.relationship:
            parent = getattr(obj, self.relationship).first()
            if parent:
                return dict(
                    (
                        key,
                        reverse(self.content_view_name, args=(parent.pk, size,)) + '?_={}'.format(hash)
                    ) for key, size in list(sizes.items())
                )
        else:
            return dict(
                (
                    key,
                    reverse('upload-image-preview', args=(obj.id, size)) + '?_={}'.format(hash)
                ) for key, size in list(sizes.items())
            )

    class Meta(object):
        model = Image
        fields = ('id', 'file', 'filename', 'owner', 'links', 'cropbox')
        meta_fields = ['filename', 'size']
