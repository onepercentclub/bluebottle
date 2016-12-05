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
    theme = serializers.CharField(source='display_theme')

    def get_aggregate_attribute(self, obj, attr):
        if obj.display:
            if 'project' in self.context:
                try:
                    aggregate = obj.aggregateanswer_set.get(project=self.context['project'],
                                                            aggregation_type='combined')
                    return getattr(aggregate, attr)
                except obj.aggregateanswer_set.model.DoesNotExist:
                    return None

            if 'start_date' in self.context and 'end_date' in self.context:
                if attr == 'value' and obj.type in ['number']:
                    return obj.get_platform_aggregate(start=self.context['start_date'],
                                                      end=self.context['end_date'])
                if attr == 'options' and obj.type in ['table-radio']:
                    return obj.get_platform_aggregate(start=self.context['start_date'],
                                                      end=self.context['end_date'])
                return None

            raise AttributeError('Need a project or a start_date and end_date to aggregate')
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
                  'theme', 'value', 'list', 'options',
                  'left_label', 'right_label',
                  'response_count',
                  'properties', 'style')


class ProjectSurveySerializer(serializers.ModelSerializer):
    answers = QuestionSerializer(many=True, read_only=True, source='questions')

    response_count = serializers.SerializerMethodField()

    def get_response_count(self, obj):
        return len(obj.response_set.filter(project=self.context['project']))

    class Meta:
        model = Survey
        fields = ('id', 'answers', 'title', 'response_count')
