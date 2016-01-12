from rest_framework import serializers

from .models import Reward


class RewardSerializer(serializers.ModelSerializer):

    count = serializers.IntgerField(source='count')

    class Meta:
        model = Reward
        fields = ('id', 'title', 'description', 'amount', 'count')
