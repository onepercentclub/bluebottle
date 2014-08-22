from django.conf import settings
from django.db import models
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


class PaymentAction(models.Model):
    """
    This is used as action to process Payment.
    For now this is only used as AuthorizationAction
    """

    class ActionTypes(DjangoChoices):
        redirect = ChoiceItem('redirect', label=_("Redirect"))
        popup = ChoiceItem('popup', label=_("Popup"))

    class ActionMethods(DjangoChoices):
        get = ChoiceItem('get', label=_("GET"))
        post = ChoiceItem('post', label=_("POST"))

    # Payment action fields. These determine the authorization step in the payment process.
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

    authorization_action = models.OneToOneField(PaymentAction, verbose_name=_("Authorization action"), null=True)

    def full_clean(self, exclude=None):
        self.amount = self.order.total

    def set_authorization_action(self, action, save=True):
        self.authorization_action = PaymentAction(**action)
        if save:
            self.save()


class Payment(PolymorphicModel):
    order_payment = models.OneToOneField('payments.OrderPayment')
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    class Meta:
        ordering = ('-created', '-updated')


class Transaction(PolymorphicModel):

    payment = models.ForeignKey('payments.Payment')
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    class Meta:
        ordering = ('-created', '-updated')
