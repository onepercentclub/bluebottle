from rest_framework import serializers

from bluebottle.members.serializers import UserPreviewSerializer
from .models import Quote


class QuoteSerializer(serializers.ModelSerializer):
    user = UserPreviewSerializer()

    class Meta:
        model = Quote
        fields = ('id', 'quote', 'user')
