from django.contrib.postgres.forms.jsonb import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _


class StripeAccount(models.Model):
    """
    Information needed to create a Stripe account
    https://stripe.com/docs/connect/required-verification-information
    """

    TYPES = (
        ('individual', _('Individual')),
        ('company', _('Company')),
    )

    remote_id = models.CharField(max_length=300, blank=True, null=True)

    user = models.ForeignKey('members.Member', null=True)
    organization = models.ForeignKey('organizations.Organization', null=True)

    # external_account >> ID
    type = models.CharField(max_length=30, choices=TYPES, default=TYPES[0][0])

    city = models.CharField(max_length=200, null=True, blank=True)
    address_line1 = models.CharField(max_length=200, null=True, blank=True)
    postal_code = models.CharField(max_length=200, null=True, blank=True)
    day_of_birth = models.DateField(null=True)
    first_name = models.CharField(max_length=200, null=True, blank=True)
    last_name = models.CharField(max_length=200, null=True, blank=True)

    tos_acceptance_date = models.DateField(null=True)
    tos_acceptance_ip = models.IPAddressField(null=True)

    # Company account
    additional_owners = models.CharField(max_length=200, null=True, blank=True)
    business_name = models.CharField(max_length=200, null=True, blank=True)
    business_tax_id = models.CharField(max_length=200, null=True, blank=True)

    personal_city = models.CharField(max_length=200, null=True, blank=True)
    personal_address_line1 = models.CharField(max_length=200, null=True, blank=True)
    personal_postal_code = models.CharField(max_length=200, null=True, blank=True)

    # verification_document >> Always proxy

    # US
    state = models.CharField(max_length=200, null=True, blank=True)
    ssn_last_4 = models.CharField(max_length=200, null=True, blank=True)
    personal_id_number = models.CharField(max_length=200, null=True, blank=True)


class StripeBankAccount(models.Model):
    remote_id = models.CharField(max_length=300, blank=True, null=True)
    object = models.CharField(max_length=200, null=True, blank=True, default='bank_account')
    account = models.CharField(max_length=200, null=True, blank=True)
    account_holder_name = models.CharField(max_length=200, null=True, blank=True)
    account_holder_type = models.CharField(max_length=200, null=True, blank=True)
    bank_name = models.CharField(max_length=200, null=True, blank=True)
    country = models.CharField(max_length=2, null=True, blank=True)
    currency = models.CharField(max_length=3, null=True, blank=True)
    default_for_currency = models.BooleanField(max_length=200, default=False)
    fingerprint = models.CharField(max_length=200, null=True, blank=True)
    last4 = models.CharField(max_length=12, null=True, blank=True)
    metadata = JSONField(null=True)
