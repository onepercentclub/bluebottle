from django.conf import settings
from django.db import models
from decimal import Decimal
from bluebottle.payments.models import Payment
from djchoices.choices import DjangoChoices, ChoiceItem
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import ModificationDateTimeField, \
    CreationDateTimeField


class VoucherPayment(Payment):
    voucher = models.OneToOneField('payments_voucher.Voucher',
                                   verbose_name=_("Voucher"),
                                   related_name='payment')

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = "Voucher Payment"
        verbose_name_plural = "Voucher Payments"

    @property
    def transaction_reference(self):
        return self.id

    def get_fee(self):
        # Fix me. Get the fee from the payment that bought the related voucher.
        return Decimal(0)

    def get_method_name(self):
        return 'Voucher'

    def get_method_icon(self):
        return 'images/payments_voucher/icons/icon-gift-card.svg'


class VoucherStatuses(DjangoChoices):
    new = ChoiceItem('new', label=_("New"))
    paid = ChoiceItem('paid', label=_("Paid"))
    cancelled = ChoiceItem('cancelled', label=_("Cancelled"))
    cashed = ChoiceItem('cashed', label=_("Cashed"))
    cashed_by_proxy = ChoiceItem('cashed_by_proxy', label=_("Cashed by us"))


class Voucher(models.Model):
    class VoucherLanguages(DjangoChoices):
        en = ChoiceItem('en', label=_("English"))
        nl = ChoiceItem('nl', label=_("Dutch"))

    amount = models.PositiveIntegerField(_("Amount"))
    currency = models.CharField(_("Currency"), max_length=3, default='EUR')

    language = models.CharField(_("Language"), max_length=2,
                                choices=VoucherLanguages.choices,
                                default=VoucherLanguages.en)
    message = models.TextField(_("Message"), blank=True, default="",
                               max_length=500)
    code = models.CharField(_("Code"), blank=True, default="", max_length=100)

    status = models.CharField(_("Status"), max_length=20,
                              choices=VoucherStatuses.choices,
                              default=VoucherStatuses.new, db_index=True)
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    sender = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_("Sender"), related_name="buyer",
                               null=True, blank=True)
    sender_email = models.EmailField(_("Sender email"))
    sender_name = models.CharField(_("Sender name"), blank=True, default="",
                                   max_length=100)

    receiver = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 verbose_name=_("Receiver"),
                                 related_name="casher", null=True, blank=True)
    receiver_email = models.EmailField(_("Receiver email"))
    receiver_name = models.CharField(_("Receiver name"), blank=True, default="",
                                     max_length=100)

    order = models.ForeignKey('orders.Order', verbose_name=_("Order"),
                              help_text=_("The order that bought this voucher"),
                              null=True)

    def __unicode__(self):
        code = "New"
        if self.code:
            code = self.code
        return code
