from bluebottle.donations.models import Donation
from rest_framework import serializers

from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.projects.serializers import \
    ProjectPreviewSerializer as BaseProjectPreviewSerializer
from bluebottle.fundraisers.models import Fundraiser
from bluebottle.orders.models import Order
from bluebottle.projects.models import Project
from bluebottle.utils.serializers import MoneySerializer, ProjectCurrencyValidator


class ManageDonationSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field='slug', queryset=Project.objects)
    fundraiser = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=Fundraiser.objects)
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects)
    amount = MoneySerializer()
    status = serializers.CharField(read_only=True)

    validators = [ProjectCurrencyValidator()]

    def validate_reward(self, reward):
        if (
            reward and
            not (self.instance and reward == self.instance.reward) and
            (reward.limit and reward.count >= reward.limit)
        ):
            raise serializers.ValidationError('Reward out of stock')

        return reward

    def validate(self, data):
        if 'reward' in data:
            if data['reward'] and data['reward'].amount.currency != data['amount'].currency:
                raise serializers.ValidationError(
                    'Currency must match reward currency'
                )
            if data['reward'] and data['reward'].amount.amount > data['amount'].amount:
                raise serializers.ValidationError(
                    'Amounts can not be less than the reward amount'
                )

        return data

    class Meta:
        model = Donation
        fields = ('id', 'project', 'fundraiser', 'amount', 'status', 'order',
                  'anonymous', 'completed', 'created', 'reward')

        # FIXME Add validations for amount and project phase


class PreviewDonationSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(read_only=True)
    fundraiser = serializers.PrimaryKeyRelatedField(required=False,
                                                    queryset=Fundraiser.objects)
    payment_method = serializers.SerializerMethodField()
    user = UserPreviewSerializer(source='public_user')
    amount = MoneySerializer()

    class Meta:
        model = Donation
        fields = ('id', 'project', 'fundraiser', 'user', 'created',
                  'anonymous', 'amount', 'reward', 'payment_method')

    def get_payment_method(self, obj):
        return obj.get_payment_method()


class PreviewDonationWithoutAmountSerializer(PreviewDonationSerializer):
    payment_method = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = ('id', 'project', 'fundraiser', 'user', 'created',
                  'anonymous', 'payment_method')

    def get_payment_method(self, obj):
        return obj.get_payment_method()


class DefaultDonationSerializer(PreviewDonationSerializer):
    class Meta:
        model = Donation
        fields = PreviewDonationSerializer.Meta.fields + ('amount', 'reward')


class LatestDonationProjectSerializer(BaseProjectPreviewSerializer):
    task_count = serializers.IntegerField()
    owner = UserPreviewSerializer()

    class Meta(BaseProjectPreviewSerializer):
        model = BaseProjectPreviewSerializer.Meta.model
        fields = ('id', 'title', 'image', 'status', 'pitch', 'country',
                  'task_count', 'allow_overfunding', 'is_campaign',
                  'amount_asked', 'amount_donated', 'amount_needed',
                  'deadline', 'status', 'owner')


class LatestDonationSerializer(serializers.ModelSerializer):
    project = LatestDonationProjectSerializer()
    payment_method = serializers.SerializerMethodField()
    user = UserPreviewSerializer()
    amount = MoneySerializer()

    class Meta:
        model = Donation
        fields = ('id', 'project', 'fundraiser', 'user', 'created',
                  'anonymous', 'amount', 'payment_method')

    def get_payment_method(self, obj):
        return obj.get_payment_method()
