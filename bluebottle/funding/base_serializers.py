from builtins import object
from rest_framework.serializers import ModelSerializer
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.funding.models import Donor, Payment, BankAccount, PayoutAccount
from bluebottle.transitions.serializers import AvailableTransitionsField
from bluebottle.utils.fields import FSMField


class PaymentSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    donation = ResourceRelatedField(queryset=Donor.objects.all())

    transitions = AvailableTransitionsField()

    class Meta(object):
        model = Payment
        fields = ('donation', 'status', )
        meta_fields = ('transitions', 'created', 'updated', )

    class JSONAPIMeta(object):
        included_resources = ['donation', 'donation.activity', 'donation.updates']
        resource_name = 'payments'

    included_serializers = {
        'donation': 'bluebottle.funding.serializers.DonorSerializer',
        'donation.updates': 'bluebottle.updates.serializers.UpdateSerializer',
        'donation.activity': 'bluebottle.funding.serializers.FundingSerializer',
    }


class BaseBankAccountSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    connect_account = ResourceRelatedField(queryset=PayoutAccount.objects.all())

    class Meta(object):
        model = BankAccount

        fields = (
            'id',
            'connect_account',
            'status',
        )

    included_serializers = {
        'connect_account': 'bluebottle.funding.serializers.PayoutAccountSerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/external-accounts'
