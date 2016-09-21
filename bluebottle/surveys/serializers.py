from rest_framework import serializers

from bluebottle.surveys.models import Survey, Question


class QuestionSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    def get_value(self, obj):
        try:
            return obj.aggregateanswer_set.get(project=self.context['project']).value
        except obj.aggregateanswer_set.model.DoesNotExist:
            return None

    class Meta:
        model = Question
        fields = ('id', 'title', 'value', 'type', 'properties')


class ProjectSurveySerializer(serializers.ModelSerializer):
    answers = QuestionSerializer(many=True, read_only=True, source='question_set')

    class Meta:
        model = Survey
        fields = ('id', 'answers', 'title')
