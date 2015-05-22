from rest_framework import serializers
from bluebottle.suggestions.models import Suggestion


class DateField(serializers.CharField):

    def from_native(self, value):
        try:
            return value.split('T')[0]
        except IndexError:
            return value

# class PublicSuggestionSerializer(serializers.ModelSerializer):
#     deadline = DateField()
#
#     class Meta:
#         model = Suggestion
#         exclude = ('token', )
#
#
# class SuggestionSerializer(PublicSuggestionSerializer):
#     project = serializers.SlugRelatedField(slug_field='slug', required=False)

import uuid

def generate_token():
    return str(uuid.uuid4())

class SuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suggestion

    deadline = DateField()
    token = serializers.CharField(required=False, default=generate_token)
    project = serializers.SlugRelatedField(slug_field='slug', required=False)
