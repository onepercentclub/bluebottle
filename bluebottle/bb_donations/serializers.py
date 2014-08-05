# coding=utf-8
from bluebottle.utils.utils import get_serializer_class, get_model_class
from rest_framework import serializers

DONATION_MODEL = get_model_class('DONATIONS_DONATION_MODEL')


class ManageDonationSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(source='project', slug_field='slug')
    status = serializers.ChoiceField(read_only=True)
    order = serializers.PrimaryKeyRelatedField()
    amount = serializers.DecimalField()

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'user', 'amount', 'status', 'order')

    # FIXME Add validations for amount and project phase


class DonationSerializer(serializers.ModelSerializer):
    project = get_serializer_class('PROJECTS_PROJECT_MODEL', 'preview')
    user = get_serializer_class('AUTH_USER_MODEL', 'preview')

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'user', 'created')
