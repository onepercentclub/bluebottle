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
    bank_account_token = serializers.CharField(write_only=True, required=False, allow_blank=True)
    account_id = serializers.CharField(read_only=True)

    legal_entity = serializers.SerializerMethodField()
    bank_account = serializers.SerializerMethodField()
    verification = serializers.SerializerMethodField()

    def get_legal_entity(self, obj):
        try:
            legal_entity = stripe.Account.retrieve(
                obj.account_id, api_key=get_secret_key()
            ).legal_entity.to_dict()

            return dict((key, value) for key, value in legal_entity.items() if key != 'verification')
        except AttributeError:
            return {}

    def get_verification(self, obj):
        try:
            return stripe.Account.retrieve(
                obj.account_id, api_key=get_secret_key()
            ).legal_entity.verification.to_dict()
        except AttributeError:
            return {}

    def get_bank_account(self, obj):
        try:
            return stripe.Account.retrieve(
                obj.account_id, api_key=get_secret_key()
            ).external_accounts.data[0].to_dict()
        except (AttributeError, IndexError):
            return {}

    def create_stripe_account(self, data):
        account_token = data.pop('account_token', None)
        if account_token:
            secret_key = get_secret_key()
            account = stripe.Account.create(
                account_token=account_token,
                country=data['country'],
                type='custom',
                payout_schedule={'interval': 'manual'},
                api_key=secret_key
            )

            data['account_id'] = account.id
            return account

    def update_stripe_account(self, instance, account, data):
        account_token = data.pop('account_token', None)
        if account_token:
            account.account_token = account_token
            account.save()

    def set_stripe_bank_account(self, account, data):
        bank_account_token = data.pop('bank_account_token', None)
        if bank_account_token:
            account.external_account = bank_account_token
            account.save()

    def create(self, data):
        account = self.create_stripe_account(data)
        self.set_stripe_bank_account(account, data)
        return super(StripePayoutAccountSerializer, self).create(data)

    def update(self, instance, data):
        secret_key = get_secret_key()
        if instance.account_id:
            account = stripe.Account.retrieve(instance.account_id, api_key=secret_key)
            self.update_stripe_account(instance, account, data)
        else:
            account = self.create_stripe_account(data)

        self.set_stripe_bank_account(account, data)
        return super(StripePayoutAccountSerializer, self).update(instance, data)

    class Meta:
        model = StripePayoutAccount
        fields = (
            'id',
            'account_token',
            'bank_account_token',
            'country',
            'account_id',
            'verified',
            'bank_account',
            'verification',
            'legal_entity',
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
