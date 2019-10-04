from rest_framework import serializers
from rest_framework.permissions import IsAdminUser

from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.files.serializers import PrivateDocumentField
from bluebottle.utils.fields import ValidationErrorsField, RequiredErrorsField, FSMField
from bluebottle.funding.models import PlainPayoutAccount


class PlainPayoutAccountSerializer(serializers.ModelSerializer):
    document = PrivateDocumentField(required=False, allow_null=True, permissions=[IsAdminUser])
    owner = ResourceRelatedField(read_only=True)
    status = FSMField(read_only=True)

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'external_accounts': 'bluebottle.funding.serializers.BankAccountSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'document': 'bluebottle.funding.serializers.KycDocumentSerializer',
    }

    class Meta:
        model = PlainPayoutAccount

        fields = (
            'id',
            'owner',
            'status',
            'document',
            'required',
            'errors',
        )
        meta_fields = ('required', 'errors', 'status')

    class JSONAPIMeta():
        resource_name = 'payout-accounts/plains'
        included_resources = [
            'external_accounts',
            'owner',
            'document'
        ]
