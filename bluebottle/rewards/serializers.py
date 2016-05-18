from rest_framework import serializers

from .models import Reward


class RewardSerializer(serializers.ModelSerializer):

    project = serializers.SlugRelatedField(slug_field="slug", queryset=Reward.objects)
    count = serializers.IntegerField(source='count', read_only=True)

    class Meta:
        model = Reward
        fields = ('id', 'title', 'description', 'amount', 'limit', 'project', 'count')
