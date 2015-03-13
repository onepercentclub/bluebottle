from bluebottle.bb_accounts.serializers import UserPreviewSerializer
from rest_framework import serializers

from .models import Quote


class QuoteSerializer(serializers.ModelSerializer):
    user = UserPreviewSerializer()

    class Meta:
        model = Quote
        fields = ('id', 'quote', 'user')
