from rest_framework import serializers

from bluebottle.projects.models import Project
from .models import Reward


class RewardSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field="slug", queryset=Project.objects)
    count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Reward
        fields = ('id', 'title', 'description', 'amount', 'limit', 'project', 'count')
