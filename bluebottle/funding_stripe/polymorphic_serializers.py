from bluebottle.funding_stripe.models import ExternalAccount, StripePayoutAccount

from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework import serializers


class ExternalAccountSerializer(serializers.ModelSerializer):
    connect_account = ResourceRelatedField(queryset=StripePayoutAccount.objects.all())
    token = serializers.CharField(write_only=True)

    account_holder_name = serializers.CharField(read_only=True, source='account.account_holder_name')
    country = serializers.CharField(read_only=True, source='account.country')
    last4 = serializers.CharField(read_only=True, source='account.last4')
    currency = serializers.CharField(read_only=True, source='account.currency')
    routing_number = serializers.CharField(read_only=True, source='account.routing_number')

    included_serializers = {
        'connect_account': 'bluebottle.funding_stripe.serializers.ConnectAccountSerializer',
    }

    class Meta:
        model = ExternalAccount

        fields = (
            'id', 'token', 'connect_account', 'account_holder_name',
            'country', 'last4', 'currency', 'routing_number'
        )

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/stripe-external-accounts'
        included_resources = ['connect-account']
