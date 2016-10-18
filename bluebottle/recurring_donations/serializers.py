from bluebottle.recurring_donations.models import (MonthlyDonor,
                                                   MonthlyDonorProject)
from rest_framework import serializers
from bluebottle.projects.models import Project
from bluebottle.utils.serializers import MoneySerializer


class MonthlyDonationProjectSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(many=False, slug_field='slug',
                                           queryset=Project.objects)
    donation = serializers.PrimaryKeyRelatedField(source='donor',
                                                  queryset=MonthlyDonor.objects)

    class Meta():
        model = MonthlyDonorProject
        fields = ('id', 'donation', 'project')


class MonthlyDonationSerializer(serializers.ModelSerializer):
    projects = MonthlyDonationProjectSerializer(many=True, read_only=True)
    amount = MoneySerializer()

    class Meta():
        model = MonthlyDonor
        fields = ('id', 'amount', 'iban', 'bic', 'active', 'name', 'city',
                  'country', 'projects')
