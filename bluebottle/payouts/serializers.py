from rest_framework import serializers
import stripe

from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.clients import properties
from bluebottle.payouts.models import PayoutAccount
from bluebottle.payouts.models.plain import PlainPayoutAccount, PayoutDocument
from bluebottle.payouts.models.stripe import StripePayoutAccount
from bluebottle.payments_stripe.utils import get_secret_key
from bluebottle.utils.permissions import ResourceOwnerPermission


from rest_polymorphic.serializers import PolymorphicSerializer


class BasePayoutAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = PayoutAccount
        fields = ('id', 'created')


class PayoutDocumentSerializer(serializers.ModelSerializer):

    file = PrivateFileSerializer(
        'payout-document-file',
        file_attr='file',
        url_args=('pk', ),
        permission=ResourceOwnerPermission
    )

    class Meta:
        model = PayoutDocument
        fields = ('id', 'file')


class PlainPayoutAccountSerializer(serializers.ModelSerializer):

    document = serializers.PrimaryKeyRelatedField(queryset=PayoutDocument.objects, required=False, allow_null=True)

    class Meta:
        model = PlainPayoutAccount
        fields = (
            'id',
            'type',
            'account_holder_name',
            'account_holder_address',
            'account_holder_postal_code',
            'account_holder_city',
            'account_holder_country',
            'account_number',
            'account_details',
            'account_bank_country',
            'document'
        )


class StripePayoutAccountSerializer(serializers.ModelSerializer):
    account_token = serializers.CharField(write_only=True, required=False, allow_blank=True)
    account_id = serializers.CharField(read_only=True)

    external_data = serializers.SerializerMethodField()

    def get_external_data(self, obj):
        return stripe.Account.retrieve(
            obj.account_id, api_key=get_secret_key()
        ).to_dict()

    def create(self, data):
        account_token = data.pop('account_token', None)
        if account_token:
            account = stripe.Account.create(
                account_token=account_token,
                country=data['country'],
                type='custom',
                api_key=get_secret_key()
            )
            data['account_id'] = account.id

        return super(StripePayoutAccountSerializer, self).create(data)

    def update(self, instance, data):
        account_token = data.pop('account_token', None)
        if account_token:
            secret_key = get_secret_key()
            if instance.account_id:
                account = stripe.Account.retrieve(instance.account_id, api_key=secret_key)
                account.account_token = account_token
                response = account.save()
            else:
                response = stripe.Account.create(
                    account_token=account_token,
                    country=data['country'],
                    type='custom',
                    api_key=secret_key
                )
                data['account_id'] = response.id

        return super(StripePayoutAccountSerializer, self).update(instance, data)

    class Meta:
        model = StripePayoutAccount
        fields = (
            'id',
            'account_token',
            'country',
            'account_id',
            'verified',
            'external_data',
        )


class PayoutAccountSerializer(PolymorphicSerializer):

    resource_type_field_name = 'type'

    def to_resource_type(self, model_or_instance):
        return model_or_instance.type

    model_serializer_mapping = {
        PayoutAccount: BasePayoutAccountSerializer,
        StripePayoutAccount: StripePayoutAccountSerializer,
        PlainPayoutAccount: PlainPayoutAccountSerializer
    }


class PayoutMethodSerializer(serializers.Serializer):

    class Meta:
        fields = (
            'type',
            'countries',
            'data'
        )
