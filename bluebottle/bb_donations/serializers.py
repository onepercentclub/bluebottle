# coding=utf-8
from bluebottle.utils.model_dispatcher import get_donation_model
from bluebottle.utils.serializer_dispatcher import get_serializer_class
from rest_framework import serializers

DONATION_MODEL = get_donation_model()


class ManageDonationSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field='slug')
    fundraiser = serializers.PrimaryKeyRelatedField(required=False)
    order = serializers.PrimaryKeyRelatedField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField(source='status', read_only=True)

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'fundraiser', 'amount', 'status', 'order', 'anonymous', 'completed', 'created')

    # FIXME Add validations for amount and project phase


class PreviewDonationSerializer(serializers.ModelSerializer):
    project = get_serializer_class('PROJECTS_PROJECT_MODEL', 'preview')
    fundraiser = serializers.PrimaryKeyRelatedField(required=False)
    user = get_serializer_class('AUTH_USER_MODEL', 'preview')(source='public_user')

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'fundraiser', 'user', 'created', 'anonymous', 'amount')


class DefaultDonationSerializer(PreviewDonationSerializer):
    class Meta:
        model = DONATION_MODEL
        fields = PreviewDonationSerializer.Meta.fields + ('amount',)
