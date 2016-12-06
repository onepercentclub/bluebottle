from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.projects.models import Project
from bluebottle.statistics.statistics import Statistics
from rest_framework import serializers

from bluebottle.cms.models import (
    Stat, StatsContent, ResultPage,
    QuotesContent, SurveyContent, Quote,
    ProjectImagesContent, ProjectsContent
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
        model = QuotesContent
        fields = ('stats', 'title', 'sub_title')


class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = ('name', 'quote')


class QuotesContentSerializer(serializers.ModelSerializer):
    quotes = QuoteSerializer(source='quotes.quote_set', many=True)

    class Meta:
        model = QuotesContent
        fields = ('quotes', 'title', 'sub_title')


class SurveyContentSerializer(serializers.ModelSerializer):
    answers = QuestionSerializer(many=True, source='survey.visible_questions')
    response_count = serializers.SerializerMethodField()

    def get_response_count(self, obj):
        return 'unknown'

    class Meta:
        model = SurveyContent
        fields = ('id', 'response_count', 'answers', 'title', 'sub_title')


class ProjectImageSerializer(serializers.ModelSerializer):
    photo = ImageSerializer(source='image')

    class Meta:
        model = Project
        fields = ('photo', 'title', 'slug')


class ProjectImagesContentSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    def get_images(self, obj):
        projects = Project.objects.filter(
            campaign_ended__gte=self.context['start_date'].strftime('%Y-%m-%d 00:00+00:00'),
            campaign_ended__lte=self.context['end_date'].strftime('%Y-%m-%d 00:00+00:00'),
            status__slug__in=['done-complete', 'done-incomplete']).order_by('?')
        return ProjectImageSerializer(projects, many=True).to_representation(projects)

    class Meta:
        model = ProjectImagesContent
        fields = ('id', 'images', 'title', 'sub_title', 'description',
                  'action_text', 'action_link')


class ProjectContentSerializer(serializers.Serializer):
    projects = ProjectPreviewSerializer(many=True, source='projects.projects')
    title = serializers.CharField()
    sub_title = serializers.CharField()
    action = serializers.CharField()
    action_text = serializers.CharField()

    class Meta:
        fields = ('id', 'title', 'sub_title')


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
        if isinstance(obj, ProjectImagesContent):
            return ProjectImagesContentSerializer(obj, context=self.context).to_representation(obj)
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
