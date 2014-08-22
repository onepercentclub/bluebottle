# coding=utf-8
from bluebottle.utils.model_dispatcher import get_donation_model
from bluebottle.utils.serializer_dispatcher import get_serializer_class
from rest_framework import serializers

DONATION_MODEL = get_donation_model()


class ManageDonationSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(source='project', slug_field='slug')
    status = serializers.ChoiceField(read_only=True)
    order = serializers.PrimaryKeyRelatedField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'user', 'amount', 'status', 'order', 'anonymous')

    # FIXME Add validations for amount and project phase


class DonationSerializer(serializers.ModelSerializer):
    project = get_serializer_class('PROJECTS_PROJECT_MODEL', 'preview')
    user = get_serializer_class('AUTH_USER_MODEL', 'preview')

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'user', 'created', 'anonymous')
