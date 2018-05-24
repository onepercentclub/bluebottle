import uuid

from rest_framework import serializers

from bluebottle.suggestions.models import Suggestion
from bluebottle.projects.models import Project


class DateField(serializers.CharField):
    def to_internal_value(self, value):
        try:
            return value.split('T')[0]
        except IndexError:
            return value


def generate_token():
    return str(uuid.uuid4())


class SuggestionSerializer(serializers.ModelSerializer):
    deadline = DateField()
    project = serializers.SlugRelatedField(slug_field='slug', required=False,
                                           queryset=Project.objects)
    token = serializers.CharField(required=False, default=generate_token)

    class Meta:
        model = Suggestion
        fields = '__all__'
