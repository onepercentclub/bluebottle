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
    name = serializers.CharField(required=False)

    validators = [ProjectCurrencyValidator()]

    class Meta:
        model = Donation
        fields = (
            'amount',
            'anonymous',
            'completed',
            'created',
            'fundraiser',
            'id',
            'name',
            'order',
            'project',
            'reward',
            'status'
        )


class PreviewDonationSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(read_only=True)
    fundraiser = serializers.PrimaryKeyRelatedField(required=False,
                                                    queryset=Fundraiser.objects)
    payment_method = serializers.SerializerMethodField()
    user = UserPreviewSerializer(source='public_user')
    amount = MoneySerializer()
    name = serializers.CharField(required=False)

    class Meta:
        model = Donation
        fields = (
            'amount',
            'anonymous',
            'created',
            'fundraiser',
            'id',
            'name',
            'payment_method',
            'project',
            'reward',
            'user'
        )

    def get_payment_method(self, obj):
        return obj.get_payment_method()


class PreviewDonationWithoutAmountSerializer(PreviewDonationSerializer):
    payment_method = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = (
            'anonymous',
            'created',
            'fundraiser',
            'id',
            'name',
            'payment_method',
            'project',
            'user'
        )

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
        fields = (
            'allow_overfunding',
            'amount_asked',
            'amount_donated',
            'amount_needed',
            'country',
            'deadline',
            'id',
            'image',
            'is_campaign',
            'owner',
            'pitch',
            'status',
            'status',
            'task_count',
            'title'
        )


class LatestDonationSerializer(serializers.ModelSerializer):
    project = LatestDonationProjectSerializer()
    payment_method = serializers.SerializerMethodField()
    user = UserPreviewSerializer()
    amount = MoneySerializer()

    class Meta:
        model = Donation
        fields = (
            'amount',
            'anonymous',
            'created',
            'fundraiser',
            'id',
            'name',
            'payment_method',
            'project',
            'user'
        )

    def get_payment_method(self, obj):
        return obj.get_payment_method()
