from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem
from django.db.models import options

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer','preview_serializer', 'manage_serializer')


class DonationStatuses(DjangoChoices):
    new = ChoiceItem('new', label=_("New"))
    in_progress = ChoiceItem('in_progress', label=_("In progress"))
    pending = ChoiceItem('pending', label=_("Pending"))
    paid = ChoiceItem('paid', label=_("Paid"))
    failed = ChoiceItem('failed', label=_("Failed"))


class BaseDonation(models.Model):
    """
    Donation of an amount from a user to a project.
    """
    amount = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2)

    # User is just a cache of the order user.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"), null=True, blank=True)
    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL, verbose_name=_("Project"))
    fundraiser = models.ForeignKey(settings.FUNDRAISERS_FUNDRAISER_MODEL, verbose_name=_("Fund raiser"), null=True, blank=True)

    order = models.ForeignKey(settings.ORDERS_ORDER_MODEL, verbose_name=_("Order"), related_name='donations', null=True, blank=True)

    status = models.CharField(_("Status"), max_length=20, choices=DonationStatuses.choices, default=DonationStatuses.new, db_index=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    completed = models.DateTimeField(_("Ready"), blank=True, editable=False, null=True)

    anonymous = models.BooleanField(_("Anonymous"), default=False)

    class Meta:
        abstract = True
        default_serializer = 'bluebottle.bb_donations.serializers.DonationSerializer'
        preview_serializer = 'bluebottle.bb_donations.serializers.DonationSerializer'
        manage_serializer = 'bluebottle.bb_donations.serializers.ManageDonationSerializer'


