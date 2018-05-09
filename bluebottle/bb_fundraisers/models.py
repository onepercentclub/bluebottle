from moneyed import Money

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.aggregates import Sum
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)


from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import ImageField, MoneyField
from bluebottle.utils.utils import StatusDefinition
from bluebottle.wallposts.models import Wallpost


class BaseFundraiser(models.Model):
    owner = models.ForeignKey('members.Member',
                              verbose_name=_("initiator"),
                              help_text=_("Project owner"))
    project = models.ForeignKey('projects.Project',
                                verbose_name=_("project"))

    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    image = ImageField(_("picture"), max_length=255, blank=True, null=True,
                       upload_to='fundraiser_images/',
                       help_text=_("Minimal of 800px wide"))
    video_url = models.URLField(max_length=100, blank=True, default='')

    amount = MoneyField(_("amount"))
    deadline = models.DateTimeField(null=True)

    created = CreationDateTimeField(_("created"), help_text=_(
        "When this fundraiser was created."))
    updated = ModificationDateTimeField(_('updated'))
    deleted = models.DateTimeField(_('deleted'), blank=True, null=True)

    location = models.ForeignKey('geo.Location', null=True, blank=True)

    wallposts = GenericRelation(Wallpost, related_query_name='fundraiser_wallposts')

    def __unicode__(self):
        return self.title

    @property
    def amount_donated(self):
        donations = self.donation_set.filter(
            order__status__in=[StatusDefinition.SUCCESS,
                               StatusDefinition.PENDING,
                               StatusDefinition.PLEDGED])

        totals = [
            Money(data['amount__sum'], data['amount_currency']) for data in
            donations.values('amount_currency').annotate(Sum('amount')).order_by()
        ]

        totals = [convert(amount, self.amount.currency) for amount in totals]

        return sum(totals) or Money(0, self.amount.currency)

    class Meta():
        abstract = True
        verbose_name = _('fundraiser')
        verbose_name_plural = _('fundraisers')


