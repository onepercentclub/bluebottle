from rest_framework import serializers
from bluebottle.suggestions.models import Suggestion


class DateField(serializers.CharField):

    def from_native(self, value):
        try: 
            return value.split('T')[0]
        except IndexError:
            return value

class SuggestionSerializer(serializers.ModelSerializer):
    deadline = DateField()
    project = serializers.SlugRelatedField(slug_field='slug')

    class Meta:
        model = Suggestion
        exclude = ('token', )
