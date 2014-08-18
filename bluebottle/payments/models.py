from django.conf import settings
from django.db import models
from django.utils.text import Truncator
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem
from polymorphic.polymorphic_model import PolymorphicModel
from django.db.models import options

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('serializer', )


class OrderPaymentStatuses(DjangoChoices):
    new = ChoiceItem('new', label=_("New"))
    in_progress = ChoiceItem('in_progress', label=_("In Progress"))
    pending = ChoiceItem('pending', label=_("Pending"))
    failed = ChoiceItem('failed', label=_("Failed"))
    unknown = ChoiceItem('unknown', label=_("Unknown"))
    cancelled = ChoiceItem('cancelled', label=_("Cancelled"))
    chargedback = ChoiceItem('charged_back', label=_("Charged back"))
    paid = ChoiceItem('paid', label=_("Paid"))


class AuthorizationAction(models.Model):

    class ActionTypes(DjangoChoices):
        redirect = ChoiceItem('redirect', label=_("Redirect"))
        popup = ChoiceItem('popup', label=_("Popup"))

    class ActionMethods(DjangoChoices):
        get = ChoiceItem('get', label=_("GET"))
        post = ChoiceItem('post', label=_("POST"))

    # Authorization action fields. These determine the authorization step in the payment process.
    type = models.CharField(_("Authorization action type"), blank=True, max_length=20,
                                                 choices=ActionTypes.choices)
    method = models.CharField(_("Authorization action method"), blank=True, max_length=20,
                                                   choices=ActionMethods.choices)
    url = models.CharField(_("Authorization action url"), blank=True, max_length=500)
    payload = models.CharField(_("Authorization action payload"), blank=True, max_length=1000)


class OrderPayment(models.Model):
    """
    An order is a collection of OrderItems and vouchers with a connected payment.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), blank=True, null=True)
    order = models.ForeignKey(settings.ORDERS_ORDER_MODEL, related_name='payments')

    status = models.CharField(_("Status"), max_length=20, choices=OrderPaymentStatuses.choices,
                              default=OrderPaymentStatuses.new, db_index=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    closed = models.DateTimeField(_("Closed"), blank=True, editable=False, null=True)

    amount = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2)

    # Payment method used
    payment_method = models.CharField(max_length=20, default='', blank=True)
    payment_meta_data = models.CharField(_("Integration data"), blank=True, max_length=1000)

    authorization_action = models.OneToOneField(AuthorizationAction, verbose_name=_("Authorization action"), null=True)

    def full_clean(self, exclude=None):
        self.amount = self.order.total

    def set_authorization_action(self, action, save=True):
        self.authorization_action = AuthorizationAction(**action)
        if save:
            self.save()


class PaymentMetaDataType(DjangoChoices):
    """
    These are types of next actions to take.
    After the payment is sent to the PSP we have a resolution about what
    to do next.
    """
    # TODO: review this list.
    redirect = ChoiceItem('redirect', label=_("Redircet"))
    popup = ChoiceItem('popup', label=_("Popup"))
    done = ChoiceItem('done', label=_("Done"))


class PaymentMetaDataMethod(DjangoChoices):
    """
    These are methods to use in the next payment step.
    """
    # TODO: review this list.
    get = ChoiceItem('get', label=_("Get"))
    post = ChoiceItem('post', label=_("Post"))


class Payment(PolymorphicModel):
    order_payment = models.OneToOneField('payments.OrderPayment')
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    class Meta:
        ordering = ('-created', '-updated')
        serializer = 'bluebottle.payments.serializers.BasePaymentMetaDataSerializer'


class PaymentMethod(models.Model):

    name = models.CharField(_("name"), max_length=200)
    profile = models.CharField(_("profile"), max_length=20)
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    support_recurring = models.BooleanField(default=False)


class Transaction(PolymorphicModel):

    payment = models.ForeignKey('payments.Payment')
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    class Meta:
        ordering = ('-created', '-updated')


class TransactionStatusChange(PolymorphicModel):

    payment = models.ForeignKey('payments.Payment')
    created = CreationDateTimeField(_("Created"))


class PaymentLogLevels(DjangoChoices):
    info = ChoiceItem('info', label=_("INFO"))
    warn = ChoiceItem('warn', label=_("WARN"))
    error = ChoiceItem('error', label=_("ERROR"))


# TODO: Add fields for: source file, source line number, source version, IP
class PaymentLogEntry(models.Model):
    message = models.CharField(max_length=400)
    level = models.CharField(max_length=15, choices=PaymentLogLevels.choices)
    timestamp = CreationDateTimeField()
    payment = models.ForeignKey(Payment, related_name='log_entries')

    class Meta:
        ordering = ('-timestamp',)
        verbose_name = _("Payment Log")
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return '{0} {1}'.format(self.get_level_display(), Truncator(self.message).words(6))

    def log_entry(self):
        return '[{0}]  {1: <5}  {2 <5}  {3}'.format(self.timestamp.strftime("%d/%b/%Y %H:%M:%S"),
                                                    self.get_type_display(), self.get_level_display(), self.message)
