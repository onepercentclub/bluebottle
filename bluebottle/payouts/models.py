from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from polymorphic.models import PolymorphicModel
from stripe.error import PermissionError

from bluebottle.payments_stripe.utils import get_secret_key
from bluebottle.projects.models import Project
from bluebottle.utils.fields import PrivateFileField
from bluebottle.utils.utils import reverse_signed

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

    reviewed = models.BooleanField(
        _('Bank reviewed'),
        help_text=_(
            'Review the project documents before marking the account as reviewed. '
            'After setting the project to running, the account documents will be deleted. '
            'Also, make sure to remove the documents from your device after downloading them. '
            'In case of Euro and USD projects the documents will be reviewed by Stripe.'
        ),
        default=False
    )

    @property
    def projects(self):
        return Project.objects.filter(payout_account=self).all()

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
    document_type = models.CharField(max_length=100, null=True, blank=True)

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
    def check_status(self):
        # Bust cache
        if self.account:
            del self.account
        if self.account_details and \
                self.account_details.verification.status == 'verified':
            self.reviewed = True
        else:
            self.reviewed = False
        self.save()

    @cached_property
    def account(self):
        try:
            return stripe.Account.retrieve(self.account_id, api_key=get_secret_key())
        except PermissionError:
            return {}

    @property
    def country(self):
        return self.account.country

    @property
    def short_details(self):
        if self.account_details:
            return {
                "first name": self.account_details.first_name,
                "last name": self.account_details.last_name,
                "country": self.account_details.address.country,
                "account holder name": self.bank_details.account_holder_name,
                "account number": "*************{}".format(self.bank_details.last4) if self.bank_details.last4 else '',
                "bank country": self.bank_details.country,
                "currency": self.bank_details.currency,
            }

    @property
    def bank_details(self):
        try:
            return self.account.external_accounts.data[0]
        except IndexError:
            return None

    @property
    def account_details(self):
        return getattr(self.account, 'legal_entity', None)

    @property
    def verification(self):
        return self.account.verification

    @property
    def fields_needed(self):
        return self.verification.fields_needed

    @property
    def verification_error(self):
        if self.account_details and self.account_details.verification and self.account_details.verification.details:
            return self.account_details.verification.details
        return ''


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

    def __unicode__(self):
        return u"{}: {}".format(_("Bank details"), self.account_holder_name)

    class Meta:
        verbose_name = _('Bank details')
        verbose_name_plural = _('Bank details')
