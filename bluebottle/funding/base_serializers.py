from rest_framework.serializers import ModelSerializer
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.utils.fields import FSMField
from bluebottle.funding.models import Donation, Payment
from bluebottle.transitions.serializers import AvailableTransitionsField


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
