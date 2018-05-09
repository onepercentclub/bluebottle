from django.conf import settings
from django.db import models
from django_extensions.db.fields import CreationDateTimeField, \
    ModificationDateTimeField

from localflavor.generic.models import IBANField, BICField
from django.utils.translation import ugettext_lazy as _
from moneyed.classes import Money

from bluebottle.utils.fields import MoneyField


class MonthlyDonor(models.Model):
    """
    Information about a user that wants to donate monthly.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    active = models.BooleanField(default=True)
    amount = MoneyField(_("amount"))

    iban = IBANField()
    bic = BICField(blank=True, default='')
    name = models.CharField(max_length=35)
    city = models.CharField(max_length=35)
    country = models.ForeignKey('geo.Country', blank=True, null=True)

    @property
    def is_valid(self):
        # Check if we're above the DocData minimum for direct debit.
        if self.amount < Money(1.13, 'EUR'):
            return False

        # Check if the IBAN / BIC is stored correctly.
        if self.iban == '' or self.bic == '' or self.bic[:4] != self.iban[4:8]:
            return False

        # Check if the IBAN / BIC is match.
        # FIXME: Check if this goes for all IBAN/Bic or just just for The Netherlands.
        if self.bic[:4] != self.iban[4:8]:
            return False

        return True

    class Meta:
        verbose_name = _('monthly donor')
        verbose_name_plural = _('monthly donors')


class MonthlyDonorProject(models.Model):
    """
    Preferred projects by a monthly donor.
    """

    donor = models.ForeignKey(MonthlyDonor, related_name='projects')
    project = models.ForeignKey('projects.Project')


class MonthlyBatch(models.Model):

    BATCH_STATUSES = (
        ('new', _('New')),
        ('processing', _('Processing')),
        ('done', _('Processed')),
    )

    date = models.DateField()
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))
    status = models.CharField(max_length=20, choices=BATCH_STATUSES, default='new')

    def __unicode__(self):
        return self.date.strftime('%B %Y')

    class Meta:
        verbose_name = _('Monthly batch')
        verbose_name_plural = _('Monthly batches')


class MonthlyProject(models.Model):
    """
    Aggregated amount for projects.
    """

    batch = models.ForeignKey(MonthlyBatch)
    project = models.ForeignKey('projects.Project')
    amount = MoneyField(_("amount"), default=0)


class MonthlyOrder(models.Model):
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))

    batch = models.ForeignKey(MonthlyBatch, related_name='orders')
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    amount = MoneyField(_("Amount"), default=0)
    name = models.CharField(max_length=35)
    city = models.CharField(max_length=35)
    iban = IBANField(blank=True, default='')
    bic = BICField(blank=True, default='')
    country = models.CharField(max_length=2, default='')

    processed = models.BooleanField(
        help_text=_("Whether a payment has been created for this order."),
        default=False)
    error = models.CharField(max_length=1000, blank=True, null=True, default='')

    class Meta:
        verbose_name = _('monthly order')
        verbose_name_plural = _('monthly orders')

    def __unicode__(self):
        return "{0}: {1} {2}".format(self.user, self.amount.currency, self.amount.amount)


class MonthlyDonation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    order = models.ForeignKey(MonthlyOrder, related_name='donations')
    project = models.ForeignKey('projects.Project')
    amount = MoneyField(_("Amount"), default=0)

    class Meta:
        verbose_name = _('monthly donation')
        verbose_name_plural = _('monthly donations')
