import os
from django.core.urlresolvers import reverse

from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.files.models import Document, Image


class FileField(ResourceRelatedField):
    def get_queryset(self):
        return Document.objects.all()


class FileSerializer(ModelSerializer):
    file = serializers.FileField(write_only=True)
    filename = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField()
    owner = ResourceRelatedField(read_only=True)
    size = serializers.IntegerField(read_only=True, source='file.size')

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    def get_links(self, obj):
        return {'url': obj.file.name}

    def get_filename(self, instance):
        return os.path.basename(instance.file.name)

    class Meta:
        model = Document
        fields = ('id', 'file', 'filename', 'size', 'owner', 'links',)
        meta_fields = ['size', 'filename']

    class JSONAPIMeta:
        included_resources = ['owner', ]


class ImageField(ResourceRelatedField):
    def get_queryset(self):
        return Image.objects.all()


class ImageSerializer(FileSerializer):

    def get_links(self, obj):
        if hasattr(self, 'sizes'):
            parent_id = getattr(obj, self.relationship).get().pk
            return dict(
                (
                    key,
                    reverse(self.content_view_name, args=(parent_id, size))
                ) for key, size in self.sizes.items()
            )

    class Meta:
        model = Image
        fields = ('id', 'file', 'filename', 'size', 'owner', 'links',)
        meta_fields = ['size', 'filename']
