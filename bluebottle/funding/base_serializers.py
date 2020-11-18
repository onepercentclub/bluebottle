from builtins import object
from rest_framework.serializers import ModelSerializer
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.funding.models import Donor, Payment, BankAccount, PayoutAccount
from bluebottle.transitions.serializers import AvailableTransitionsField
from bluebottle.utils.fields import FSMField


class PaymentSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    donor = ResourceRelatedField(queryset=Donor.objects.all())

    transitions = AvailableTransitionsField()

    included_serializers = {
        'donor': 'bluebottle.funding.serializers.DonorSerializer',
    }

    class Meta(object):
        model = Payment
        fields = ('donor', 'status', )
        meta_fields = ('transitions', 'created', 'updated', )

    class JSONAPIMeta(object):
        included_resources = [
            'donation',
        ]
        resource_name = 'payments'


class BaseBankAccountSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    connect_account = ResourceRelatedField(queryset=PayoutAccount.objects.all())

    class Meta(object):
        model = BankAccount

        fields = (
            'id',
            'connect_account',
            'status'
        )

    included_serializers = {
        'connect_account': 'bluebottle.funding.serializers.PayoutAccountSerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/external-accounts'
