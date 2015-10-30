from rest_framework import serializers
from bluebottle.suggestions.models import Suggestion


class DateField(serializers.CharField):
    def from_native(self, value):
        try:
            return value.split('T')[0]
        except IndexError:
            return value


import uuid


def generate_token():
    return str(uuid.uuid4())


class SuggestionSerializer(serializers.ModelSerializer):
    deadline = DateField()
    project = serializers.SlugRelatedField(slug_field='slug', required=False)
    token = serializers.CharField(required=False, default=generate_token)

    class Meta:
        model = Suggestion
