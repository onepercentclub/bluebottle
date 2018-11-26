from django.db import models

from bluebottle.payouts.models import PayoutAccount
from django.utils.translation import ugettext_lazy as _


class PlainPayoutAccount(PayoutAccount):

    type = 'payout-plain'

    account_holder_name = models.CharField(
        _("account holder name"), max_length=100, null=True, blank=True)
    account_holder_address = models.CharField(
        _("account holder address"), max_length=255, null=True, blank=True)
    account_holder_postal_code = models.CharField(
        _("account holder postal code"), max_length=20, null=True, blank=True)
    account_holder_city = models.CharField(
        _("account holder city"), max_length=255, null=True, blank=True)
    account_holder_country = models.ForeignKey(
        'geo.Country', blank=True, null=True,
        related_name="payout_account_holder_country")

    account_number = models.CharField(_("Account number"), max_length=255,
                                      null=True, blank=True)
    account_details = models.CharField(_("account details"), max_length=500, null=True, blank=True)
    account_bank_country = models.ForeignKey(
        'geo.Country', blank=True, null=True,
        related_name="payout_account_bank_country")
