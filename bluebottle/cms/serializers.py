from rest_framework import serializers

from bluebottle.cms.models import Stat, StatsContent


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


class StatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stat
        fields = ('type', 'name')


class StatsContentSerializer(ContentTypeSerializer):
    title = serializers.CharField(source='stats.title')
    stats = StatSerializer(source='stats.stat_set')

    class Meta:
        fields = ('project', 'type')


class RegionSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if isinstance(obj, StatsContent):
            return StatsContentSerializer(obj, context=self.context).to_representation(obj)

    class Meta:
        fields = ('id')


class PageSerializer(serializers.ModelSerializer):
    title = serializers.CharField()
    main = RegionSerializer(source='content.main', many=True)

    class Meta:
        fields = ('id', 'title', 'slug', 'main')
