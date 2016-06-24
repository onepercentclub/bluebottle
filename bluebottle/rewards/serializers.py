from rest_framework import serializers

from bluebottle.projects.models import Project
from .models import Reward


class RewardSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field="slug", queryset=Project.objects)
    count = serializers.IntegerField(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=5.0)

    class Meta:
        model = Reward
        fields = ('id', 'title', 'description', 'amount', 'limit', 'project', 'count')
