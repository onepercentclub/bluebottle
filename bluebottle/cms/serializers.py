from rest_framework import serializers

from feincms.contents import RichTextContent
from feincms.module.medialibrary.contents import MediaFileContent

from bluebottle.cms.models import Page, ProjectContent
from bluebottle.projects.serializers import ProjectPreviewSerializer


class ContentTypeSerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()

    def get_type(self, obj):
        return obj.__class__.__name__


class RichTextContentSerializer(ContentTypeSerializer):
    text = serializers.CharField()

    class Meta:
        fields = ('text', 'type')


class MediaFileContentSerializer(ContentTypeSerializer):
    url = serializers.CharField(source='mediafile.file.url')
    caption = serializers.CharField(source='mediafile.translation.caption')

    def get_url(self, obj):
        return obj.file.url

    class Meta:
        fields = ('url', 'type')


class ProjectContentSerializer(ContentTypeSerializer):
    project = ProjectPreviewSerializer()

    class Meta:
        fields = ('project', 'type')


class RegionSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if isinstance(obj, RichTextContent):
            return RichTextContentSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, MediaFileContent):
            return MediaFileContentSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, ProjectContent):
            return ProjectContentSerializer(obj, context=self.context).to_representation(obj)

    class Meta:
        fields = ('id')


class PageSerializer(serializers.ModelSerializer):
    title = serializers.CharField()
    main = RegionSerializer(source='content.main', many=True)

    class Meta:
        fields = ('id', 'title', 'slug', 'main')
        model = Page
