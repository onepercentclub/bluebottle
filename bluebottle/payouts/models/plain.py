from django.db import models

from bluebottle.payouts.models import PayoutAccount
from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.fields import PrivateFileField
from bluebottle.utils.utils import reverse_signed


class PlainPayoutAccount(PayoutAccount):

    type = 'plain'
    providers = [
        'docdata', 'pledge', 'flutterwave', 'lipisha', 'vitepay', 'pledge', 'telesom',
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

    document = models.ForeignKey('payouts.PayoutDocument', null=True, blank=True)

    def __unicode__(self):
        return "{}: {}".format(_("Bank details"), self.account_holder_name)

    class Meta:
        verbose_name = _('Bank details')
        verbose_name_plural = _('Bank details')


class PayoutDocument(models.Model):

    """ Document for an Payout """

    file = PrivateFileField(
        max_length=110,
        upload_to='payouts/documents'
    )
    author = models.ForeignKey('members.Member', verbose_name=_('author'), blank=True, null=True)
    created = models.DateField(_('created'), auto_now_add=True)
    updated = models.DateField(_('updated'), auto_now=True)

    deleted = models.DateTimeField(_('deleted'), null=True, blank=True)

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
