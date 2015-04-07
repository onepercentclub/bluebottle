import json
from bluebottle.payments.exception import PaymentException

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from django_extensions.db.fields.json import JSONField
# from django_fsm import FSMField, transition
from djchoices import DjangoChoices, ChoiceItem
from polymorphic.polymorphic_model import PolymorphicModel
from django.db.models import options
from django.dispatch import receiver
from django_fsm.signals import post_transition
from django_fsm.db.fields import FSMField, transition
from django.db.models.signals import pre_save, post_save

from bluebottle.utils.utils import FSMTransition, StatusDefinition
from bluebottle.payments.managers import PaymentManager

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('serializer', )


class Payment(PolymorphicModel):
    STATUS_CHOICES = (
        (StatusDefinition.CREATED, _('Created')),
        (StatusDefinition.STARTED, _('Started')),
        (StatusDefinition.CANCELLED, _('Cancelled')),
        (StatusDefinition.AUTHORIZED, _('Authorized')),
        (StatusDefinition.SETTLED, _('Settled')),
        (StatusDefinition.CHARGED_BACK, _('Charged_back')),
        (StatusDefinition.REFUNDED, _('Refunded')),
        (StatusDefinition.FAILED, _('Failed')),
        (StatusDefinition.UNKNOWN, _('Unknown'))
    )

    @classmethod
    def get_by_order_payment(cls, order_payment):
        if len(cls.objects.filter(order_payment=order_payment).all()):
            return cls.objects.filter(order_payment=order_payment).all()[0]
        return None

    status = FSMField(default=StatusDefinition.STARTED, choices=STATUS_CHOICES, protected=False)
    previous_status = None
    order_payment = models.OneToOneField('payments.OrderPayment')
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    @property
    def method_name(self):
        return self.get_method_name()

    def get_method_name(self):
        return 'unknown'

    @property
    def method_icon(self):
        return self.get_method_icon()

    def get_method_icon(self):
        return 'images/payments/icons/icon-payment.svg'

    def get_fee(self):
        if not isinstance(self, Payment):
            raise PaymentException("get_fee() not implemented for {0}".format(self.__class__.__name__))

    class Meta:
        ordering = ('-created', '-updated')


class OrderPaymentAction(models.Model):
    """
    This is used as action to process OrderPayment.
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
    url = models.CharField(_("Authorization action url"), blank=True, max_length=2000)
    payload = models.CharField(_("Authorization action payload"), blank=True, max_length=5000)


class OrderPayment(models.Model, FSMTransition):
    """
    An order is a collection of OrderItems and vouchers with a connected payment.
    """
    STATUS_CHOICES = Payment.STATUS_CHOICES

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), blank=True, null=True)
    order = models.ForeignKey(settings.ORDERS_ORDER_MODEL, related_name='order_payments')
    status = FSMField(default=StatusDefinition.CREATED, choices=STATUS_CHOICES, protected=True)
    previous_status = None
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    closed = models.DateTimeField(_("Closed"), blank=True, editable=False, null=True)
    amount = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2)

    transaction_fee = models.DecimalField(_("Transaction Fee"), max_digits=16, decimal_places=2, null=True,
                                          help_text=_("Bank & transaction fee, withheld by payment provider."))

    # Payment method used
    payment_method = models.CharField(max_length=20, default='', blank=True)
    integration_data = JSONField(_("Integration data"), max_length=5000, blank=True)
    authorization_action = models.OneToOneField(OrderPaymentAction, verbose_name=_("Authorization action"), null=True)

    @classmethod
    def get_latest_by_order(cls, order):
        order_payments = cls.objects.order_by('-created').filter(order=order).all()
        if len(order_payments) > 0:
            return order_payments[0]
        return None

    @transition(field=status, save=True, source=StatusDefinition.CREATED, target=StatusDefinition.STARTED)
    def started(self):
        # TODO: add started state behaviour here
        pass

    @transition(field=status, save=True, source=[StatusDefinition.STARTED, StatusDefinition.CANCELLED], target=StatusDefinition.AUTHORIZED)
    def authorized(self):
        # TODO: add authorized state behaviour here
        pass

    @transition(field=status, save=True, source=[StatusDefinition.AUTHORIZED, StatusDefinition.STARTED, StatusDefinition.CANCELLED], target=StatusDefinition.SETTLED)
    def settled(self):
        self.closed = now()

    @transition(field=status, save=True, source=[StatusDefinition.STARTED, StatusDefinition.SETTLED], target=StatusDefinition.FAILED)
    def failed(self):
        self.closed = None

    @transition(field=status, save=True, source=[StatusDefinition.STARTED, StatusDefinition.FAILED], target=StatusDefinition.CANCELLED)
    def cancelled(self):
        # TODO: add cancelled state behaviour here
        pass

    @transition(field=status, save=True, source=[StatusDefinition.AUTHORIZED, StatusDefinition.SETTLED], target=StatusDefinition.CHARGED_BACK)
    def charged_back(self):
        self.closed = None

    @transition(field=status, save=True, source=StatusDefinition.AUTHORIZED, target=StatusDefinition.REFUNDED)
    def refunded(self):
        self.closed = None

    @transition(field=status, save=True, source=[StatusDefinition.STARTED, StatusDefinition.AUTHORIZED], target=StatusDefinition.UNKNOWN)
    def unknown(self):
        # TODO: add unknown state behaviour here
        pass

    def get_status_mapping(self, payment_status):
        # Currently the status in Payment and OrderPayment is one to one.
        return payment_status

    def full_clean(self, exclude=None, validate_unique=False):
        self.amount = self.order.total
        if self.id:
            # If the payment method has changed we should recalculate the fee.
            previous = OrderPayment.objects.get(id=self.id)
            try:
                self.transaction_fee = self.payment.get_fee()
            except ObjectDoesNotExist:
                pass

    def set_authorization_action(self, action, save=True):
        self.authorization_action = OrderPaymentAction(**action)
        self.authorization_action.save()

        if save:
            self.save()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super(OrderPayment, self).save(force_insert, force_update, using, update_fields)


class Transaction(PolymorphicModel):
    payment = models.ForeignKey('payments.Payment')
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    objects = PaymentManager()

    class Meta:
        ordering = ('-created', '-updated')

import signals
