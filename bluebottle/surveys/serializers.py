from rest_framework import serializers

from bluebottle.surveys.models import Survey, Question


class QuestionSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    list = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()
    response_count = serializers.SerializerMethodField()

    title = serializers.CharField(source='display_title')
    style = serializers.CharField(source='display_style')

    def get_aggregate_attribute(self, obj, attr):
        try:
            aggregate = obj.aggregateanswer_set.get(project=self.context['project'],
                                                    aggregation_type='combined')
            return getattr(aggregate, attr)
        except obj.aggregateanswer_set.model.DoesNotExist:
            return None

    def get_value(self, obj):
        return self.get_aggregate_attribute(obj, 'value')

    def get_list(self, obj):
        return self.get_aggregate_attribute(obj, 'list')

    def get_options(self, obj):
        return self.get_aggregate_attribute(obj, 'options')

    def get_response_count(self, obj):
        return self.get_aggregate_attribute(obj, 'response_count')

    def get_properties(self, obj):
        return obj.properties

    class Meta:
        model = Question
        fields = ('id', 'title', 'type', 'display',
                  'value', 'list', 'options',
                  'response_count',
                  'properties', 'style')


class ProjectSurveySerializer(serializers.ModelSerializer):
    answers = QuestionSerializer(many=True, read_only=True, source='question_set')

    response_count = serializers.SerializerMethodField()

    def get_response_count(self, obj):
        return len(obj.response_set.filter(project=self.context['project']))

    class Meta:
        model = Survey
        fields = ('id', 'answers', 'title', 'response_count')
