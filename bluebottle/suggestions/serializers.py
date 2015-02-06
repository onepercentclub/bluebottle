from rest_framework import serializers
from bluebottle.suggestions.models import Suggestion


class DateField(serializers.CharField):

    def from_native(self, value):
        return value.split('T')[0]

class SuggestionSerializer(serializers.ModelSerializer):
    deadline = DateField()

    class Meta:
        model = Suggestion


