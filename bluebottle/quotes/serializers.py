from rest_framework import serializers
from bluebottle.utils.serializer_dispatcher import get_serializer_class

from .models import Quote


class QuoteSerializer(serializers.ModelSerializer):
    user = get_serializer_class('AUTH_USER_MODEL', 'preview')()

    class Meta:
        model = Quote
        fields = ('id', 'quote', 'user')
