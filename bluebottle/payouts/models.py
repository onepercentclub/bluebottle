from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem
from polymorphic.models import PolymorphicModel

from bluebottle.bb_payouts.models import BaseProjectPayout, BaseOrganizationPayout
from bluebottle.clients import properties

from bluebottle.utils.fields import PrivateFileField
from bluebottle.utils.utils import reverse_signed

from django.utils.translation import ugettext_lazy as _
from bluebottle.payments_stripe.utils import get_secret_key

import stripe


class PayoutDocument(models.Model):

    """ Document for an Payout """

    file = PrivateFileField(
        max_length=110,
        upload_to='payouts/documents'
    )
    author = models.ForeignKey('members.Member', verbose_name=_('author'), blank=True, null=True)
    created = models.DateField(_('created'), auto_now_add=True)
    updated = models.DateField(_('updated'), auto_now=True)

    ip_address = models.GenericIPAddressField(_('IP address'), blank=True, null=True, default=None)

    class Meta:
        verbose_name = _('payout document')
        verbose_name_plural = _('payout documents')

    @property
    def document_url(self):
        # pk may be unset if not saved yet, in which case no url can be
        # generated.
        if self.pk is not None and self.file:
            return reverse_signed('payout-document-file', args=(self.pk,))
        return None

    @property
    def owner(self):
        return self.author


class PayoutAccount(PolymorphicModel):

    type = 'base'
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
    user = models.ForeignKey('members.Member')

    class Meta:
        permissions = (
            ('api_read_payoutdocument', 'Can view payout documents through the API'),
            ('api_add_payoutdocument', 'Can add payout documents through the API'),
            ('api_change_payoutdocument', 'Can change payout documents through the API'),
            ('api_delete_payoutdocument', 'Can delete payout documents through the API'),

            ('api_read_own_payoutdocument', 'Can view payout own documents through the API'),
            ('api_add_own_payoutdocument', 'Can add own payout documents through the API'),
            ('api_change_own_payoutdocument', 'Can change own payout documents through the API'),
            ('api_delete_own_payoutdocument', 'Can delete own payout documents through the API'),
        )


class StripePayoutAccount(PayoutAccount):
    type = 'stripe'

    account_id = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=2, null=True, blank=True)
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
    verification_error = models.CharField(
        max_length=100, null=True, blank=True,
        help_text=_("Reason why verification has failed")
    )

    @property
    def account(self):
        return stripe.Account.retrieve(self.account_id, api_key=get_secret_key())


class PlainPayoutAccount(PayoutAccount):

    type = 'plain'
    providers = [
        'docdata', 'pledge', 'flutterwave', 'lipisha',
        'vitepay', 'pledge', 'telesom', 'beyonic'
    ]

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

    document = models.ForeignKey('payouts.PayoutDocument', models.SET_NULL, null=True, blank=True)
    reviewed = models.BooleanField(
        _('Reviewed'),
        help_text=_(
            'Review the project documents before marking the account as reviewed.'
            'After setting the project to running, the account documents will be deleted.'
            'Also, make sure to remove the documents from your device after downloading them.'
        ),
        default=False
    )

    def __unicode__(self):
        return "{}: {}".format(_("Bank details"), self.account_holder_name)

    class Meta:
        verbose_name = _('Bank details')
        verbose_name_plural = _('Bank details')


# Legacy Payouts models

class ProjectPayout(BaseProjectPayout):
    class PayoutRules(DjangoChoices):
        """ Which rules to use to calculate fees. """
        beneath_threshold = ChoiceItem('beneath_threshold',
                                       label=_("Beneath minimal payout amount"))
        fully_funded = ChoiceItem('fully_funded', label=_("Fully funded"))
        not_fully_funded = ChoiceItem('not_fully_funded',
                                      label=_("Not fully funded"))

        # Legacy payout rules
        old = ChoiceItem('old', label=_("Legacy: Old 1%/5%"))
        zero = ChoiceItem('zero', label=_("Legacy: 0%"))
        five = ChoiceItem('five', label=_("Legacy: 5%"))
        seven = ChoiceItem('seven', label=_("Legacy: 7%"))
        twelve = ChoiceItem('twelve', label=_("Legacy: 12%"))
        hundred = ChoiceItem('hundred', label=_("Legacy: 100%"))
        unknown = ChoiceItem('unknown', label=_("Legacy: Unknown"))
        other = ChoiceItem('other', label=_("Legacy: Other"))

    # Payout rules

    def calculate_amount_payable_rule_beneath_threshold(self, total):
        """
        Calculate the amount payable for beneath_threshold rule
        """
        payable_rate = 1 - properties.PROJECT_PAYOUT_FEES['beneath_threshold']
        return total * Decimal(payable_rate)

    def calculate_amount_payable_rule_fully_funded(self, total):
        """
        Calculate the amount payable for fully_funded rule
        """
        payable_rate = 1 - properties.PROJECT_PAYOUT_FEES['fully_funded']
        return total * Decimal(payable_rate)

    def calculate_amount_payable_rule_not_fully_funded(self, total):
        """
        Calculate the amount payable for not_fully_funded rule
        """
        payable_rate = 1 - properties.PROJECT_PAYOUT_FEES['not_fully_funded']
        return total * Decimal(payable_rate)

    # Legacy payout rules

    def calculate_amount_payable_rule_old(self, total):
        """
        Calculate the amount payable for old rule
        """
        return total * Decimal(0.95)

    def calculate_amount_payable_rule_zero(self, total):
        """
        Calculate the amount payable for 0% rule
        """
        return total * Decimal(1)

    def calculate_amount_payable_rule_five(self, total):
        """
        Calculate the amount payable for 5% rule
        """
        return total * Decimal(0.95)

    def calculate_amount_payable_rule_seven(self, total):
        """
        Calculate the amount payable for 7% rule
        """
        return total * Decimal(0.93)

    def calculate_amount_payable_rule_twelve(self, total):
        """
        Calculate the amount payable for 5% rule
        """
        return total * Decimal(0.88)

    def calculate_amount_payable_rule_hundred(self, total):
        """
        Calculate the amount payable for 5% rule
        """
        return total * Decimal(0)

    def get_payout_rule(self):
        """
        Override this if you want different payout rules for different circumstances.
        e.g. project target reached, minimal amount reached.
        """
        assert self.project

        threshold = properties.MINIMAL_PAYOUT_AMOUNT

        if self.project.amount_donated.amount <= threshold:
            # Funding less then minimal payment amount.
            return self.PayoutRules.beneath_threshold
        elif self.project.amount_donated >= self.project.amount_asked:
            # Fully funded
            return self.PayoutRules.fully_funded
        else:
            # Not fully funded
            return self.PayoutRules.not_fully_funded


class OrganizationPayout(BaseOrganizationPayout):
    def _get_organization_fee(self):
        """
        Calculate and return the organization fee for Payouts within this
        OrganizationPayout's period, including VAT.

        Note: this should *only* be called internally.
        """
        # Get Payouts
        payouts = ProjectPayout.objects.filter(
            completed__gte=self.start_date,
            completed__lte=self.end_date
        )

        # Aggregate value
        aggregate = payouts.aggregate(models.Sum('organization_fee'))

        # Return aggregated value or 0.00
        fee = aggregate.get(
            'organization_fee__sum', Decimal('0.00')
        ) or Decimal('0.00')

        return fee
