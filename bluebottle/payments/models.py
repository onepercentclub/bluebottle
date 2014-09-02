import json
from django.conf import settings
from django.db import models
from django.utils.text import Truncator
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from django_extensions.db.fields.json import JSONField
from djchoices import DjangoChoices, ChoiceItem
from polymorphic.polymorphic_model import PolymorphicModel
from django.db.models import options
from django_fsm.db.fields import FSMField, transition
from django_fsm.signals import pre_transition, post_transition
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, post_delete

from bluebottle.utils.utils import FSMTransition, StatusDefinition
from bluebottle.payments.signals import (payment_status_changed, 
                                         set_previous_status,
                                         default_status_check)


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
        (StatusDefinition.UNKNOWN, _('Unknown')),
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

    class Meta:
        ordering = ('-created', '-updated')

pre_save.connect(set_previous_status,
                  sender=Payment, 
                  dispatch_uid='previous_status_model_payment')

post_save.connect(payment_status_changed, 
                  sender=Payment, 
                  dispatch_uid='change_status_model_payment')

post_save.connect(default_status_check, 
                  sender=Payment, 
                  dispatch_uid='default_status_model_payment')


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
    order = models.ForeignKey(settings.ORDERS_ORDER_MODEL, related_name='payments')
    status = FSMField(default=StatusDefinition.CREATED, choices=STATUS_CHOICES, protected=True)
    previous_status = None
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    closed = models.DateTimeField(_("Closed"), blank=True, editable=False, null=True)
    amount = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2)

    # Payment method used
    payment_method = models.CharField(max_length=20, default='', blank=True)
    integration_data = JSONField(_("Integration data"), max_length=5000, blank=True)
    authorization_action = models.OneToOneField(OrderPaymentAction, verbose_name=_("Authorization action"), null=True)

    @transition(field=status, save=True, source=StatusDefinition.CREATED, target=StatusDefinition.STARTED)
    def started(self):
        # TODO: add started state behaviour here
        pass

    @transition(field=status, save=True, source=StatusDefinition.STARTED, target=StatusDefinition.AUTHORIZED)
    def authorized(self):
        # TODO: add authorized state behaviour here
        pass

    @transition(field=status, save=True, source=StatusDefinition.AUTHORIZED, target=StatusDefinition.SETTLED)
    def settled(self):
        # TODO: add settled state behaviour here
        pass

    @transition(field=status, save=True, source=[StatusDefinition.STARTED, StatusDefinition.SETTLED], target=StatusDefinition.FAILED)
    def failed(self):
        # TODO: add failed state behaviour here
        pass

    @transition(field=status, save=True, source=[StatusDefinition.STARTED, StatusDefinition.FAILED], target=StatusDefinition.CANCELLED)
    def cancelled(self):
        # TODO: add cancelled state behaviour here
        pass

    @transition(field=status, save=True, source=StatusDefinition.AUTHORIZED, target=StatusDefinition.CHARGED_BACK)
    def charged_back(self):
        # TODO: add charged_back state behaviour here
        pass

    @transition(field=status, save=True, source=StatusDefinition.AUTHORIZED, target=StatusDefinition.REFUNDED)
    def refunded(self):
        # TODO: add refunded state behaviour here
        pass

    @transition(field=status, save=True, source=[StatusDefinition.STARTED, StatusDefinition.AUTHORIZED], target=StatusDefinition.UNKNOWN)
    def unknown(self):
        # TODO: add unknown state behaviour here
        pass

    def get_status_mapping(self, payment_status):
        # Currently the status in Payment and OrderPayment is one to one.
        return payment_status

    def full_clean(self, exclude=None):
        self.amount = self.order.total

    def set_authorization_action(self, action, save=True):
        self.authorization_action = OrderPaymentAction(**action)
        self.authorization_action.save()

        if save:
            self.save()

pre_save.connect(set_previous_status,
                  sender=OrderPayment, 
                  dispatch_uid='previous_status_model_order_payment')

post_save.connect(default_status_check, 
                  sender=OrderPayment, 
                  dispatch_uid='default_status_model_order_payment')


class Transaction(PolymorphicModel):
    payment = models.ForeignKey('payments.Payment')
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    class Meta:
        ordering = ('-created', '-updated')


@receiver(post_save, weak=False, sender=OrderPayment, dispatch_uid='order_payment_model')
def order_payment_changed(sender, instance, **kwargs):
    # Send status change notification when record first created
    # This is to ensure any components listening for a status 
    # on an OrderPayment will also receive the initial status.

    # Get the default status for the status field on OrderPayment
    default_status = OrderPayment._meta.get_field_by_name('status')[0].get_default()

    # Signal new status if current status is the default value
    if (instance.status == default_status):
        signal_kwargs = {
            'sender': sender,
            'instance': instance,
            'target': instance.status
        }
        post_transition.send(**signal_kwargs)
