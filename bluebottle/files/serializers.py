import os
from django.core.urlresolvers import reverse
from django.conf import settings

from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.files.models import File


class FileField(ResourceRelatedField):
    def __init__(self, content_view_name, sizes, *args, **kwargs):
        self.content_view_name = content_view_name
        self.sizes = sizes

        super(FileField, self).__init__(*args, **kwargs)

    def get_queryset(self):
        return File.objects.all()

    def get_links(self, instance, pk_field):
        return dict(
            (
                size,
                reverse(self.content_view_name, args=(instance.pk, size))
            ) for size in self.sizes
        )


class FileSerializer(ModelSerializer):
    file = serializers.FileField(write_only=True)
    created = serializers.DateTimeField(read_only=True)
    filename = serializers.SerializerMethodField()
    size = serializers.IntegerField(read_only=True, source='file.size')
    owner = ResourceRelatedField(read_only=True)

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    def get_filename(self, instance):
        return  os.path.basename(instance.file.name)

    class Meta:
        model = File
        fields = ('id', 'file', 'created', 'filename', 'size', 'owner', )

    class JSONAPIMeta:
        included_resources = ['owner', ]
