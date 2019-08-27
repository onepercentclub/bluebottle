from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import (
    ModelSerializer, ValidationError, IntegerField)

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer,
    ActivityValidationSerializer
)
from bluebottle.files.serializers import ImageField
from bluebottle.funding.filters import DonationListFilter
from bluebottle.funding.models import Funding, Donation, Payment, Fundraiser, Reward, BudgetLine, PaymentMethod
from bluebottle.members.models import Member
from bluebottle.transitions.serializers import AvailableTransitionsField
from bluebottle.transitions.serializers import TransitionSerializer
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import MoneySerializer, FilteredRelatedField, NonModelRelatedResourceField, \
    ResourcePermissionField


class FundingCurrencyValidator(object):
    """
    Validates that the currency of the field is the same as the activity currency
    """
    message = _('Currency does not match any of the activities currencies')

    def __init__(self, fields=None, message=None):
        if fields is None:
            fields = ['amount']

        self.fields = fields
        self.message = message or self.message

    def __call__(self, data):
        for field in self.fields:
            if data[field].currency != data['activity'].target.currency:
                raise ValidationError(self.message)


class FundraiserSerializer(ModelSerializer):
    """
    Serializer to view/create fundraisers
    """
    owner = ResourceRelatedField(read_only=True)
    activity = ResourceRelatedField(queryset=Funding.objects.all())
    image = ImageField(required=False, allow_null=True)

    amount = MoneySerializer()
    amount_donated = MoneySerializer(read_only=True)

    validators = [FundingCurrencyValidator()]

    included_serializers = {
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class Meta:
        model = Fundraiser
        fields = (
            'id', 'owner', 'activity', 'title', 'description', 'image',
            'amount', 'amount_donated', 'deadline'
        )

    class JSONAPIMeta:
        included_resources = [
            'image',
            'owner',
            'activity',
        ]

        resource_name = 'activities/fundraisers'

    def validate(self, data):
        if data.get('deadline') and data['deadline'] > data['activity'].deadline:
            raise ValidationError(
                {'deadline': [_("Fundraiser deadline exceeds activity deadline.")]}
            )
        return data


class RewardSerializer(ModelSerializer):
    activity = ResourceRelatedField(queryset=Funding.objects.all())
    count = IntegerField(read_only=True)
    amount = MoneySerializer(min_amount=5.00)

    validators = [FundingCurrencyValidator()]

    included_serializers = {
        'activity': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class Meta:
        model = Reward
        fields = ('id', 'title', 'description', 'amount', 'limit', 'activity', 'count')

    class JSONAPIMeta:
        included_resources = [
            'activity',
        ]

        resource_name = 'activities/rewards'


class BudgetLineSerializer(ModelSerializer):
    activity = ResourceRelatedField(queryset=Funding.objects.all())
    amount = MoneySerializer()

    validators = [FundingCurrencyValidator()]

    included_serializers = {
        'activity': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class Meta:
        model = BudgetLine
        fields = ('activity', 'amount', 'description')

    class JSONAPIMeta:
        included_resources = [
            'activity',
        ]

        resource_name = 'activities/budgetlines'


class PaymentMethodSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    currencies = serializers.ListField()
    countries = serializers.ListField()

    class Meta():
        model = PaymentMethod
        fields = ('code', 'name', 'currencies', 'countries', 'activity')

    class JSONAPIMeta:
        resource_name = 'payments/payment-methods'


class FundingValidationSerializer(ActivityValidationSerializer):
    target = MoneySerializer(required=False, allow_null=True)

    class Meta:
        model = Funding
        fields = ActivityValidationSerializer.Meta.fields + (
            'target',
        )

    class JSONAPIMeta:
        resource_name = 'activities/funding-validations'


class FundingListSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('funding-detail', view_args=('pk',))
    validations = NonModelRelatedResourceField(FundingValidationSerializer)
    payment_methods = PaymentMethodSerializer(many=True, read_only=True)

    class Meta(BaseActivitySerializer.Meta):
        model = Funding
        fields = BaseActivitySerializer.Meta.fields + (
            'deadline',
            'duration',
            'target',
            'budgetlines',
            'fundraisers',
            'rewards',
            'payment_methods',
            'permissions',
            'validations',
        )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        included_resources = [
            'owner',
            'initiative',
            'initiative.image',
            'location',
            'validations',
        ]
        resource_name = 'activities/funding'

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'validations': 'bluebottle.events.serializers.EventValidationSerializer',
    }


class FundingSerializer(BaseActivitySerializer):
    target = MoneySerializer(required=False, allow_null=True)

    fundraisers = FundraiserSerializer(many=True, required=False)
    rewards = RewardSerializer(many=True, required=False)
    budgetlines = BudgetLineSerializer(many=True, required=False)
    payment_methods = PaymentMethodSerializer(many=True, read_only=True)
    contributions = FilteredRelatedField(many=True, filter_backend=DonationListFilter)

    class Meta(BaseActivitySerializer.Meta):
        model = Funding
        fields = BaseActivitySerializer.Meta.fields + (
            'deadline',
            'duration',
            'target',
            'budgetlines',
            'fundraisers',
            'rewards',
            'payment_methods'
        )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        included_resources = BaseContributionSerializer.JSONAPIMeta.included_resources + [
            'image',
            'owner',
            'initiative',
            'place',
            'fundraisers',
            'budgetlines',
            'payment_methods',
            'rewards',
            'contributions',
        ]
        resource_name = 'activities/fundings'

    included_serializers = {
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'place': 'bluebottle.geo.serializers.GeolocationSerializer',
        'fundraisers': 'bluebottle.funding.serializers.FundraiserSerializer',
        'rewards': 'bluebottle.funding.serializers.RewardSerializer',
        'budgetlines': 'bluebottle.funding.serializers.BudgetLineSerializer',
        'payment_methods': 'bluebottle.funding.serializers.PaymentMethodSerializer',
        'contributions': 'bluebottle.funding.serializers.DonationSerializer',
    }


class FundingTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Funding.objects.all())
    field = 'transitions'
    included_serializers = {
        'resource': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class JSONAPIMeta:
        included_resources = ['resource', ]
        resource_name = 'funding-transitions'


class IsRelatedToActivity(object):
    """
    Validates that the reward activity is the same as the donation activity
    """
    message = _('The selected reward is not related to this activity')

    def __init__(self, field):
        self.field = field

    def __call__(self, data):
        if self.field in data and not data[self.field].activity == data['activity']:
            raise ValidationError(self.message)


def reward_amount_matches(data):
    """
    Validates that the reward activity is the same as the donation activity
    """
    if 'reward' in data and not data['reward'].amount == data['amount']:
        raise ValidationError(
            _('The amount does not match the selected reward.')
        )


class DonationMemberValidator(object):
    """
    Validates that the reward activity is the same as the donation activity
    """
    message = _('User can only be set, not changed.')

    def set_context(self, serializer):
        if serializer.instance:
            self.user = serializer.instance.user
        else:
            self.user = None

    def __call__(self, data):
        if data.get('user') and data['user'].is_authenticated and self.user and self.user != data['user']:
            raise ValidationError(self.message)


class DonationSerializer(BaseContributionSerializer):
    amount = MoneySerializer()

    user = ResourceRelatedField(
        queryset=Member.objects.all(),
        default=serializers.CurrentUserDefault(),
        allow_null=True,
        required=False
    )

    included_serializers = {
        'activity': 'bluebottle.funding.serializers.FundingSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'reward': 'bluebottle.funding.serializers.RewardSerializer',
        'fundraiser': 'bluebottle.funding.serializers.FundraiserSerializer',
    }

    validators = [
        IsRelatedToActivity('reward'),
        IsRelatedToActivity('fundraiser'),
        DonationMemberValidator(),
        reward_amount_matches,
    ]

    class Meta(BaseContributionSerializer.Meta):
        model = Donation
        fields = BaseContributionSerializer.Meta.fields + ('amount', 'fundraiser', 'reward', )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        resource_name = 'contributions/donations'
        included_resources = [
            'user',
            'activity',
            'reward',
            'fundraiser',
        ]


class DonationCreateSerializer(DonationSerializer):
    amount = MoneySerializer()

    class Meta(DonationSerializer.Meta):
        model = Donation
        fields = DonationSerializer.Meta.fields + ('client_secret', )


class PaymentSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    donation = ResourceRelatedField(queryset=Donation.objects.all())

    transitions = AvailableTransitionsField()

    included_serializers = {
        'donation': 'bluebottle.funding.serializers.DonationSerializer',
    }

    class Meta:
        model = Payment
        fields = ('donation', 'status', )
        meta_fields = ('transitions', 'created', 'updated', )

    class JSONAPIMeta:
        included_resources = [
            'donation',
        ]
        resource_name = 'payments'
