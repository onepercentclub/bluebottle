# coding=utf-8
from rest_framework import serializers
from .models import Donation

class DonationSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(source='project', slug_field='slug')
    status = serializers.ChoiceField(read_only=True)

    order = serializers.PrimaryKeyRelatedField()

    amount = serializers.DecimalField()

    class Meta:
        model = Donation
        fields = ('id', 'project', 'amount', 'status', 'order')

    # FIXME Add validations for amount and project phase
