from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem
from uuidfield import UUIDField

from django.contrib.auth import get_user_model

USER_MODEL = get_user_model()


class OrderStatuses(DjangoChoices):
    cart = ChoiceItem('cart', label=_("Cart"))
    frozen = ChoiceItem('frozen', label=_("Frozen"))
    closed = ChoiceItem('closed', label=_("Closed"))


class Order(models.Model):
    """
    An order is a collection of OrderItems and vouchers with a connected payment.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=OrderStatuses.choices, default=OrderStatuses.cart, db_index=True)

    uuid = UUIDField(verbose_name=("Order number"), auto=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    closed = models.DateTimeField(_("Closed"), blank=True, editable=False, null=True)

    amount = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2)


class OrderItem(models.Model):
    """
    An OrderItem connects an item, like Donation to an Order
    """
    amount = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2)
    order = models.ForeignKey('orders.Order', verbose_name=_("Order"), null=True, blank=True)

    # Replace this with Generic Foreign Key.
    donation = models.ForeignKey('donations.Donation', verbose_name=_("Donation"), null=True, blank=True)
