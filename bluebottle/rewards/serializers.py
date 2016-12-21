from rest_framework import serializers

from bluebottle.projects.models import Project
from bluebottle.utils.serializers import MoneySerializer, ProjectCurrencyValidator
from .models import Reward


class RewardSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field="slug", queryset=Project.objects)
    count = serializers.IntegerField(read_only=True)
    amount = MoneySerializer(min_amount=5.00)

    validators = [ProjectCurrencyValidator()]

    class Meta:
        model = Reward
        fields = ('id', 'title', 'description', 'amount', 'limit', 'project', 'count')
