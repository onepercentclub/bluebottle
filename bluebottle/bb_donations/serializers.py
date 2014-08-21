# coding=utf-8
from bluebottle.utils.utils import get_serializer_class, get_model_class
from rest_framework import serializers

DONATION_MODEL = get_model_class('DONATIONS_DONATION_MODEL')


class ManageDonationSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field='slug')
    fundraiser = serializers.PrimaryKeyRelatedField()
    status = serializers.ChoiceField(read_only=True)
    order = serializers.PrimaryKeyRelatedField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'fundraiser', 'user', 'amount', 'status', 'order')

    # FIXME Add validations for amount and project phase


class DonationSerializer(serializers.ModelSerializer):
    project = get_serializer_class('PROJECTS_PROJECT_MODEL', 'preview')
    fundraiser = serializers.PrimaryKeyRelatedField()
    user = get_serializer_class('AUTH_USER_MODEL', 'preview')

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'fundraiser', 'user', 'created')
