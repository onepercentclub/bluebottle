from bluebottle.suggestions.models import Suggestion
from rest_framework import serializers


class SuggestionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Suggestion
        fields = ('title',)

        