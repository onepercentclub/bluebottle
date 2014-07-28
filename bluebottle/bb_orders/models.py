from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem
from uuidfield import UUIDField
from django.db.models import options

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer','preview_serializer', 'manage_serializer')


class OrderStatuses(DjangoChoices):
    cart = ChoiceItem('cart', label=_("Cart"))
    frozen = ChoiceItem('frozen', label=_("Frozen"))
    closed = ChoiceItem('closed', label=_("Closed"))


class BaseOrder(models.Model):
    """
    An order is a collection of OrderItems and vouchers with a connected payment.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=OrderStatuses.choices, default=OrderStatuses.cart, db_index=True)

    uuid = UUIDField(verbose_name=("Order number"), auto=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    closed = models.DateTimeField(_("Closed"), blank=True, editable=False, null=True)

    total = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2, default=0)

    class Meta:
        abstract = True
        default_serializer = 'bluebottle.bb_orders.serializers.OrderSerializer'
        preview_serializer = 'bluebottle.bb_orders.serializers.OrderSerializer'
        manage_serializer = 'bluebottle.bb_orders.serializers.ManageOrderSerializer'
