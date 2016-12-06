from bluebottle.statistics.statistics import Statistics
from rest_framework import serializers

from bluebottle.cms.models import (
    Stat, StatsContent, ResultPage, QuotesContent, SurveyContent,
    Quote, ProjectsContent
)
from bluebottle.projects.serializers import ProjectPreviewSerializer
from bluebottle.surveys.serializers import QuestionSerializer


class RichTextContentSerializer(serializers.Serializer):
    text = serializers.CharField()

    class Meta:
        fields = ('text', 'type')


class MediaFileContentSerializer(serializers.Serializer):
    url = serializers.CharField(source='mediafile.file.url')
    caption = serializers.CharField(source='mediafile.translation.caption')

    def get_url(self, obj):
        return obj.file.url

    class Meta:
        fields = ('url', 'type')


class StatSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    def get_value(self, obj):
        if obj.value:
            return obj.value
        return getattr(Statistics(start=self.context['start_date'],
                                  end=self.context['end_date']), obj.type, 0)

    class Meta:
        model = Stat
        fields = ('id', 'type', 'title', 'value')


class StatsContentSerializer(serializers.Serializer):
    stats = StatSerializer(source='stats.stat_set', many=True)
    title = serializers.CharField()
    sub_title = serializers.CharField()

    class Meta:
        fields = ('stats', 'title', 'sub_title')


class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = ('name', 'quote')


class QuotesContentSerializer(serializers.Serializer):
    quotes = QuoteSerializer(source='quotes.quote_set', many=True)
    title = serializers.CharField()
    sub_title = serializers.CharField()

    class Meta:
        fields = ('quotes', 'title', 'sub_title')


class SurveyContentSerializer(serializers.Serializer):
    answers = QuestionSerializer(many=True, source='survey.visible_questions')
    response_count = serializers.SerializerMethodField()
    title = serializers.CharField()
    sub_title = serializers.CharField()

    def get_response_count(self, obj):
        return 'unknown'

    class Meta:
        fields = ('id', 'response_count', 'title', 'sub_title')


class ProjectContentSerializer(serializers.Serializer):
    projects = ProjectPreviewSerializer(many=True, source='projects.projects')
    title = serializers.CharField()
    sub_title = serializers.CharField()
    action = serializers.CharField()
    action_text = serializers.CharField()

    def get_response_count(self, obj):
        return 'unknown'

    class Meta:
        fields = ('id', 'response_count', 'title', 'sub_title')


class BlockSerializer(serializers.Serializer):

    content = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    def get_type(self, obj):
        return obj.type

    def get_id(self, obj):
        return obj.id

    def get_content(self, obj):
        if isinstance(obj, StatsContent):
            return StatsContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, QuotesContent):
            return QuotesContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, SurveyContent):
            return SurveyContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, ProjectsContent):
            return ProjectContentSerializer(obj, context=self.context).to_representation(obj)

    class Meta:
        fields = ('id', 'type', 'content')


class ResultPageSerializer(serializers.ModelSerializer):
    blocks = BlockSerializer(source='content.contentitems', many=True)

    class Meta:
        model = ResultPage
        fields = ('id', 'title', 'slug', 'start_date',
                  'end_date', 'description', 'blocks')
