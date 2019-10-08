from rest_framework.serializers import ModelSerializer
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.funding.models import Donation, Payment, BankAccount, PayoutAccount
from bluebottle.transitions.serializers import AvailableTransitionsField
from bluebottle.utils.fields import FSMField


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


class BaseBankAccountSerializer(ModelSerializer):
    connect_account = ResourceRelatedField(queryset=PayoutAccount.objects.all())

    class Meta:
        model = BankAccount

        fields = (
            'id',
            'connect_account'
        )

    included_serializers = {
        'connect_account': 'bluebottle.funding.serializers.PayoutAccountSerializer',
    }

    class JSONAPIMeta:
        resource_name = 'payout-accounts/external-accounts'
