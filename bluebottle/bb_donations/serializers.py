# coding=utf-8
from bluebottle.bluebottle_drf2.serializers import EuroField
from bluebottle.bb_projects.models import ProjectPhase
from django.utils.translation import ugettext as _
from rest_framework import serializers
from .models import Donation, DonationStatuses

class DonationSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(source='project', slug_field='slug')
    status = serializers.ChoiceField(read_only=True)

    order = serializers.PrimaryKeyRelatedField()

    amount = serializers.DecimalField()

    class Meta:
        model = Donation
        fields = ('id', 'project', 'amount', 'status', 'order')

    # FIXME Add validations for amount and project phase
