from django.db import connection
from rest_framework import serializers

import stripe

from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.payments_stripe.utils import get_secret_key
from bluebottle.payouts.models import PayoutAccount, PlainPayoutAccount, PayoutDocument, StripePayoutAccount
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
            legal_entity = obj.account.legal_entity.to_dict()
            return dict((key, value) for key, value in legal_entity.items() if key != 'verification')
        except AttributeError:
            return {}

    def get_verification(self, obj):
        try:
            return obj.account.legal_entity.verification.to_dict()
        except AttributeError:
            return {}

    def get_bank_account(self, obj):
        try:
            return obj.account.external_accounts.data[0].to_dict()
        except (AttributeError, IndexError):
            return {}

    def create_stripe_account(self, data):
        account_token = data.pop('account_token', None)
        if account_token:
            tenant = connection.tenant
            secret_key = get_secret_key()
            account = stripe.Account.create(
                account_token=account_token,
                country=data['country'],
                type='custom',
                payout_schedule={'interval': 'manual'},
                api_key=secret_key,
                metadata={
                    "tenant_name": tenant.client_name,
                    "tenant_domain": tenant.domain_url
                },
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
        if instance.account_id:
            if instance.country != data['country']:
                if not instance.reviewed:
                    # It is not possible to change the country of an account
                    # So as long as it was not reviewed, we delete it and
                    # create a new one
                    instance.account_id = None
                    account = self.create_stripe_account(data)
                else:
                    raise serializers.ValidationError(
                        'Cannot update information after it has been reviewed'
                    )
            else:
                account = instance.account
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
            'reviewed',
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
