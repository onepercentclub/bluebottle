from rest_framework import serializers

from bluebottle.cms.models import Stat, StatsContent, ResultPage, QuotesContent, ResultsContent, Quote


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
    value = serializers.CharField(source='calculated_value')

    class Meta:
        model = Stat
        fields = ('type', 'name', 'value')


class StatsContentSerializer(ContentTypeSerializer):
    title = serializers.CharField(source='stats.name')
    stats = StatSerializer(source='stats.stat_set', many=True)

    class Meta:
        fields = ('stats', 'title')


class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = ('name', 'quote')


class QuotesContentSerializer(ContentTypeSerializer):
    title = serializers.CharField(source='quotes.name')
    quotes = QuoteSerializer(source='quotes.quote_set', many=True)

    class Meta:
        fields = ('quotes', 'title')


class ResultsContentSerializer(ContentTypeSerializer):

    class Meta:
        fields = ('id', )


class RegionSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if isinstance(obj, StatsContent):
            return StatsContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, QuotesContent):
            return QuotesContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, ResultsContent):
            return ResultsContentSerializer(obj, context=self.context).to_representation(obj)

    class Meta:
        fields = ('id')


class ResultPageSerializer(serializers.ModelSerializer):
    blocks = RegionSerializer(source='content.contentitems', many=True)

    class Meta:
        model = ResultPage
        fields = ('id', 'title', 'start_date', 'end_date', 'description', 'blocks')
