# coding=utf-8
from bluebottle.utils.utils import get_project_serializer, get_serializer_model
from rest_framework import serializers
from .models import Donation


class MyDonationSerializer(serializers.ModelSerializer):
    # project = get_serializer_model('PROJECTS_PROJECT_MODEL', 'preview')

    status = serializers.ChoiceField(read_only=True)
    order = serializers.PrimaryKeyRelatedField()
    amount = serializers.DecimalField()

    class Meta:
        model = Donation
        fields = ('id', 'project', 'user', 'amount', 'status', 'order')

    # FIXME Add validations for amount and project phase


class DonationSerializer(serializers.ModelSerializer):
    project = get_serializer_model('PROJECTS_PROJECT_MODEL', 'preview')
    user = get_serializer_model('AUTH_USER_MODEL', 'preview')

    class Meta:
        model = Donation
        fields = ('id', 'project', 'user')
