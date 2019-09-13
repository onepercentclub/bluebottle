from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from django_extensions.db.fields.json import JSONField

from djchoices import DjangoChoices, ChoiceItem
from polymorphic.models import PolymorphicModel
from django_fsm import FSMField, transition

from bluebottle import clients
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.managers import PaymentManager
from bluebottle.utils.fields import LegacyMoneyField as MoneyField
from bluebottle.utils.utils import FSMTransition, StatusDefinition


def trim_tenant_url(max_length, tenant_url):
    """
    Trims the url of a tenant so that it does not exceed max_length
    and includes three dots in the middle
    """
    length = len(tenant_url)

    # We add three dots
    diff = abs(max_length - length - 3)
    split_at = length / 2 - (diff / 2) - 3
    tenant_url = ''.join((tenant_url[:split_at],
                          '...',
                          tenant_url[split_at + diff:]))
    return tenant_url


class Payment(PolymorphicModel):
    STATUS_CHOICES = (
        (StatusDefinition.CREATED, _('Created')),
        (StatusDefinition.STARTED, _('Started')),
        (StatusDefinition.CANCELLED, _('Cancelled')),
        (StatusDefinition.PLEDGED, _('Pledged')),
        (StatusDefinition.AUTHORIZED, _('Authorized')),
        (StatusDefinition.SETTLED, _('Settled')),
        (StatusDefinition.CHARGED_BACK, _('Charged_back')),
        (StatusDefinition.REFUND_REQUESTED, _('Refund requested')),
        (StatusDefinition.REFUNDED, _('Refunded')),
        (StatusDefinition.FAILED, _('Failed')),
        (StatusDefinition.UNKNOWN, _('Unknown'))
    )

    @classmethod
    def get_by_order_payment(cls, order_payment):
        if len(cls.objects.filter(order_payment=order_payment).all()):
            return cls.objects.filter(order_payment=order_payment).all()[0]
        return None

    status = FSMField(
        default=StatusDefinition.STARTED, choices=STATUS_CHOICES,
        protected=False)
    previous_status = None
    order_payment = models.OneToOneField('payments.OrderPayment')
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    @property
    def method_name(self):
        return self.get_method_name()

    def get_method_name(self):
        return 'unknown'

    def get_fee(self):
        if not isinstance(self, Payment):
            raise PaymentException("get_fee() not implemented for "
                                   "{0}".format(self.__class__.__name__))

    @property
    def status_code(self):
        return ""

    @property
    def status_description(self):
        return ""

    class Meta:
        ordering = ('-created', '-updated')
        verbose_name = _('payment')
        verbose_name_plural = _('payments')


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

    # Payment action fields. These determine the authorization step in the
    # payment process.
    type = models.CharField(_("Authorization action type"), blank=True,
                            max_length=20,
                            choices=ActionTypes.choices)
    method = models.CharField(_("Authorization action method"), blank=True,
                              max_length=20,
                              choices=ActionMethods.choices)
    url = models.CharField(
        _("Authorization action url"), blank=True, max_length=2000)
    payload = models.CharField(
        _("Authorization action payload"), blank=True, max_length=5000)


class OrderPayment(models.Model, FSMTransition):
    """
    An order is a collection of OrderItems and vouchers with a connected
    payment.
    """
    STATUS_CHOICES = Payment.STATUS_CHOICES

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("user"), blank=True,
        null=True)
    order = models.ForeignKey('orders.Order', related_name='order_payments')
    status = FSMField(
        default=StatusDefinition.CREATED, choices=STATUS_CHOICES,
        protected=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    closed = models.DateTimeField(
        _("Closed"), blank=True, editable=False, null=True)
    amount = MoneyField(_("Amount"))

    transaction_fee = models.DecimalField(_("Transaction Fee"), max_digits=16,
                                          decimal_places=2, null=True,
                                          help_text=_(
                                              "Bank & transaction fee, withheld by payment provider."))

    # Payment method used
    payment_method = models.CharField(max_length=60, default='', blank=True)
    integration_data = JSONField(
        _("Integration data"), max_length=5000, blank=True)
    authorization_action = models.OneToOneField(
        OrderPaymentAction, verbose_name=_("Authorization action"), null=True)

    previous_status = None
    card_data = None

    @property
    def project(self):
        return self.order.donations.first().project

    class Meta:
        permissions = (
            ('refund_orderpayment', 'Can refund order payments'),
        )
        verbose_name = _('order payment')
        verbose_name_plural = _('order payments')

    @classmethod
    def get_latest_by_order(cls, order):
        order_payments = cls.objects.order_by(
            '-created').filter(order=order).all()
        if len(order_payments) > 0:
            return order_payments[0]
        return None

    @transition(field=status, source=StatusDefinition.CREATED,
                target=StatusDefinition.STARTED)
    def started(self):
        pass

    @transition(field=status, source=StatusDefinition.CREATED,
                target=StatusDefinition.PLEDGED)
    def pledged(self):
        pass

    @transition(field=status, source=[StatusDefinition.STARTED,
                                      StatusDefinition.CANCELLED,
                                      StatusDefinition.FAILED],
                target=StatusDefinition.AUTHORIZED)
    def authorized(self):
        pass

    @transition(field=status, source=[StatusDefinition.AUTHORIZED,
                                      StatusDefinition.STARTED,
                                      StatusDefinition.CANCELLED,
                                      StatusDefinition.REFUNDED,
                                      StatusDefinition.REFUND_REQUESTED,
                                      StatusDefinition.FAILED,
                                      StatusDefinition.UNKNOWN],
                target=StatusDefinition.SETTLED)
    def settled(self):
        self.closed = now()

    @transition(field=status,
                source=[StatusDefinition.STARTED,
                        StatusDefinition.AUTHORIZED,
                        StatusDefinition.REFUND_REQUESTED,
                        StatusDefinition.REFUNDED,
                        StatusDefinition.CANCELLED,
                        StatusDefinition.PENDING,
                        StatusDefinition.SETTLED],
                target=StatusDefinition.FAILED)
    def failed(self):
        self.closed = None

    @transition(field=status, source=[StatusDefinition.STARTED,
                                      StatusDefinition.FAILED],
                target=StatusDefinition.CANCELLED)
    def cancelled(self):
        pass

    @transition(field=status, source=[StatusDefinition.AUTHORIZED,
                                      StatusDefinition.SETTLED],
                target=StatusDefinition.CHARGED_BACK)
    def charged_back(self):
        self.closed = None

    @transition(
        field=status,
        source=[
            StatusDefinition.AUTHORIZED, StatusDefinition.SETTLED,
            StatusDefinition.REFUND_REQUESTED, StatusDefinition.PLEDGED
        ],
        target=StatusDefinition.REFUNDED
    )
    def refunded(self):
        self.closed = None

    @transition(field=status, source=[StatusDefinition.STARTED,
                                      StatusDefinition.AUTHORIZED,
                                      StatusDefinition.SETTLED],
                target=StatusDefinition.UNKNOWN)
    def unknown(self):
        pass

    @transition(
        field=status,
        source=[
            StatusDefinition.AUTHORIZED,
            StatusDefinition.SETTLED
        ],
        target=StatusDefinition.REFUND_REQUESTED
    )
    def refund_requested(self):
        pass

    def get_status_mapping(self, payment_status):
        # Currently the status in Payment and OrderPayment is one to one.
        return payment_status

    def set_authorization_action(self, action, save=True):
        self.authorization_action = OrderPaymentAction(**action)
        self.authorization_action.save()

        if save:
            self.save()

    @property
    def status_code(self):
        try:
            return self.payment.status_code
        except Payment.DoesNotExist:
            return ""

    @property
    def status_description(self):
        try:
            return self.payment.status_description
        except Payment.DoesNotExist:
            return ""

    @property
    def can_refund(self):
        return self.status in ('settled', 'success', )

    @property
    def info_text(self):
        """
        The description on the payment receipt.
        """
        tenant_url = clients.utils.tenant_site().domain

        docdata_max_length = 50

        if tenant_url == 'onepercentclub.com':
            info_text = _('%(tenant_url)s donation %(payment_id)s')
            # 10 chars for ' donation ' and 6 chars for the payment id
            max_tenant_chars = docdata_max_length - 10 - len(str(self.id))
        else:
            info_text = _('%(tenant_url)s via goodup %(payment_id)s')
            # 20 chars for ' via onepercentclub ' and 6 chars
            # for the payment id
            max_tenant_chars = docdata_max_length - 20 - len(str(self.id))

        length = len(tenant_url)

        if length > max_tenant_chars:
            # Note that trimming the url will change the translation string
            # This change will occur when the payment id adds a number, so
            # every now and then we'll need to update the transstring.
            tenant_url = trim_tenant_url(max_tenant_chars, tenant_url)

        return info_text % {'tenant_url': tenant_url, 'payment_id': self.id}

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.amount = self.order.total
        self.card_data = self.integration_data
        self.integration_data = {}
        if self.id:
            # If the payment method has changed we should recalculate the fee.
            try:
                self.transaction_fee = self.payment.get_fee()
            except ObjectDoesNotExist:
                pass

        super(OrderPayment, self).save(
            force_insert, force_update, using, update_fields)


class Transaction(PolymorphicModel):
    payment = models.ForeignKey('payments.Payment')
    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))

    objects = PaymentManager()

    class Meta:
        ordering = ('-created', '-updated')


import signals  # noqa
