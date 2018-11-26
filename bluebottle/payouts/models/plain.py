from django.db import models

from bluebottle.payouts.models import PayoutAccount


class PlainPayoutAccount(PayoutAccount):

    type = 'payout-plain'

    account_holder_name = models.CharField(max_length=200, null=True, blank=True)
    account_number = models.CharField(max_length=200, null=True, blank=True)
    account_details = models.CharField(max_length=200, null=True, blank=True)
    account_holder_city = models.CharField(max_length=200, null=True, blank=True)
    account_holder_country = models.CharField(max_length=200, null=True, blank=True)
