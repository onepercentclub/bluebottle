from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.payouts.models import PayoutAccount


class StripePayoutAccount(PayoutAccount):
    type = 'stripe'

    account_token = models.CharField(max_length=100, null=True, blank=True)
    verified = models.DateField(null=True, blank=True)
    providers = [
        'stripe', 'pledge',
    ]

    """
    scan_corrupt, the supplied ID image is corrupt
    scan_failed_greyscale, the supplied ID image is not in color
    scan_failed_other, the scan failed for another reason
    scan_id_country_not_supported, the country of the supplied ID is not supported
    scan_id_type_not_supported, the supplied ID type is not supported (e.g., is not government-issued
    scan_name_mismatch, the name on the ID does not match the name on the account
    scan_not_readable, the supplied ID image is not readable (e.g., too blurry or dark)
    scan_not_uploaded, no ID scan was uploaded
    failed_keyed_identity, the supplied identity information could not be verified
    failed_other, verification failed for another reason
    """
    verification_error = models.CharField(max_length=100, null=True, blank=True,
                                          help_text=_("Reason why verification has failed"))
