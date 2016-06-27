from bluebottle.donations.models import Donation
from rest_framework import serializers

from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.projects.serializers import \
    ProjectPreviewSerializer as BaseProjectPreviewSerializer, ProjectPreviewSerializer
from bluebottle.fundraisers.models import Fundraiser
from bluebottle.orders.models import Order
from bluebottle.projects.models import Project

class ManageDonationSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field='slug', queryset=Project.objects)
    fundraiser = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=Fundraiser.objects)
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects)
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, max_value=1500000
    )
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Donation
        fields = ('id', 'project', 'fundraiser', 'amount', 'status', 'order',
                  'anonymous', 'completed', 'created', 'reward')

        # FIXME Add validations for amount and project phase


class PreviewDonationSerializer(serializers.ModelSerializer):
    project = ProjectPreviewSerializer()
    fundraiser = serializers.PrimaryKeyRelatedField(required=False,
                                                    queryset=Fundraiser.objects)
    payment_method = serializers.SerializerMethodField()
    user = UserPreviewSerializer(source='public_user')

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

    class Meta:
        model = Donation
        fields = ('id', 'project', 'fundraiser', 'user', 'created',
                  'anonymous', 'amount', 'payment_method')

    def get_payment_method(self, obj):
        return obj.get_payment_method()

