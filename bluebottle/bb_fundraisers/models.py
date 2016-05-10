from django.db import models
from django.db.models import options
from django.db.models.aggregates import Sum
from django.utils.translation import ugettext as _

from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)

from bluebottle.utils.fields import ImageField
from bluebottle.utils.utils import GetTweetMixin, StatusDefinition

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer',
                                                 'preview_serializer',
                                                 'manage_serializer')


class BaseFundraiser(models.Model, GetTweetMixin):
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

    amount = models.DecimalField(_("amount"), decimal_places=2, max_digits=10)
    currency = models.CharField(max_length="10", default='EUR')
    deadline = models.DateTimeField(null=True)

    created = CreationDateTimeField(_("created"), help_text=_(
        "When this fundraiser was created."))
    updated = ModificationDateTimeField(_('updated'))
    deleted = models.DateTimeField(_('deleted'), blank=True, null=True)

    location = models.ForeignKey('geo.Location', null=True, blank=True)

    def __unicode__(self):
        return self.title

    @property
    def amount_donated(self):
        donations = self.donation_set.filter(
            order__status__in=[StatusDefinition.SUCCESS,
                               StatusDefinition.PENDING])
        if donations:
            total = donations.aggregate(sum=Sum('amount'))
            return total['sum']
        return 0.0

    class Meta():
        abstract = True
        default_serializer = 'bluebottle.fundraisers.serializers.BaseFundraiserSerializer'
        preview_serializer = 'bluebottle.fundraisers.serializers.BaseFundraiserSerializer'
        manage_serializer = 'bluebottle.fundraisers.serializers.BaseFundraiserSerializer'
