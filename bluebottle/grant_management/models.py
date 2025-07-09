# -*- coding: utf-8 -*-
import logging
from builtins import object

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import SET_NULL
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_quill.fields import QuillField
from djchoices import ChoiceItem, DjangoChoices
from moneyed import Money

from bluebottle.activities.models import Activity, Contributor
from bluebottle.clients import properties
from bluebottle.fsm.triggers import TriggerMixin
from bluebottle.funding.validators import TargetValidator
from bluebottle.funding_stripe.utils import get_stripe
from bluebottle.utils.fields import MoneyField
from bluebottle.utils.utils import get_current_host, get_current_language

logger = logging.getLogger(__name__)


class GrantProvider(models.Model):
    """
    A provider of grants, e.g. a foundation or government body.
    """

    FREQUENCY_CHOICES = (
        ("weekly", _("Weekly")),
        ("biweekly", _("Biweekly")),
        ("monthly", _("Monthly")),
        ("quarterly", _("Quarterly")),
        ("yearly", _("Yearly")),
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=200, blank=True, null=True)
    payment_frequency = models.CharField(
        max_length=100, choices=FREQUENCY_CHOICES, default="weekly"
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        verbose_name = _("Grant provider")
        verbose_name_plural = _("Grant providers")

    def __str__(self):
        return self.name or f"Grant Provider #{self.pk}"


class GrantPayment(TriggerMixin, models.Model):
    """
    A payment made to a grant donor.
    """

    total = MoneyField(default=Money(0, "EUR"), null=True, blank=True)
    status = models.CharField(max_length=40)
    grant_provider = models.ForeignKey(
        GrantProvider, null=True, on_delete=models.SET_NULL
    )
    checkout_id = models.CharField(max_length=500, null=True, blank=True)
    payment_link = models.URLField(max_length=500, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid_on = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        verbose_name = _("Grant payment")
        verbose_name_plural = _("Grant payments")

    def __str__(self):
        return f"Grant Payment #{self.pk}"

    @property
    def donors(self):
        donors = []
        for payout in self.payouts.all():
            for donor in payout.grants.all():
                donors.append(donor)

        return donors

    @cached_property
    def checkout_link(self):
        if self.checkout_id:
            stripe = get_stripe()
            session = stripe.checkout.Session.retrieve(self.checkout_id)
            return session.url
        return None

    def check_status(self):
        if self.checkout_id:
            stripe = get_stripe()
            session = stripe.checkout.Session.retrieve(self.checkout_id)
            if session.status == "complete":
                self.states.succeed()
                self.save()
        return None

    def generate_payment_link(self):
        stripe = get_stripe()
        currency = str(self.total.currency)
        init_args = {}
        bank_transfer_type = "eu_bank_transfer"
        if currency == "USD":
            bank_transfer_type = "us_bank_transfer"
        elif currency == "GBP":
            bank_transfer_type = "gb_bank_transfer"
        elif currency == "MXN":
            bank_transfer_type = "mx_bank_transfer"

        if currency == "EUR":
            init_args["payment_method_options"] = {
                "customer_balance": {
                    "funding_type": "bank_transfer",
                    "bank_transfer": {
                        "type": bank_transfer_type,
                        "eu_bank_transfer": {"country": "NL"},
                    },
                },
            }
        else:
            init_args["payment_method_options"] = {
                "customer_balance": {
                    "funding_type": "bank_transfer",
                    "bank_transfer": {
                        "type": bank_transfer_type,
                    },
                },
            }

        line_items = []
        donations = GrantDonor.objects.filter(payout__payment=self).all()

        for donation in donations:
            product = stripe.Product.create(
                name=donation.activity.title,
                description=f"Payment for grant {donation.activity.title} for fund {donation.fund.name}",
            )
            price = stripe.Price.create(
                unit_amount=int(donation.amount.amount * 100),
                currency=donation.amount.currency,
                product=product["id"],
            )
            line_items.append(
                {
                    "price": price.id,
                    "quantity": 1,
                }
            )

        init_args["payment_method_types"] = ["customer_balance", "ideal", "card"]
        init_args["line_items"] = line_items
        init_args["customer"] = self.grant_provider.stripe_customer_id
        init_args["success_url"] = get_current_host()
        checkout = stripe.checkout.Session.create(mode="payment", **init_args)
        self.checkout_id = checkout.id
        self.payment_link = checkout.url
        self.save()

    def save(self, run_triggers=True, *args, **kwargs):
        if self.id and self.total.amount == 0 and self.payouts.exists():
            for payout in self.payouts.all():
                self.total.amount += payout.total_amount
        super().save(run_triggers, *args, **kwargs)


class GrantPayout(TriggerMixin, models.Model):
    activity = models.ForeignKey(
        'grant_management.GrantApplication',
        verbose_name=_("Grant application"),
        related_name="payouts",
        on_delete=models.CASCADE
    )
    provider = models.CharField(max_length=100)
    currency = models.CharField(max_length=5)
    payment = models.ForeignKey(
        GrantPayment,
        null=True,
        blank=True,
        related_name="payouts",
        on_delete=models.SET_NULL,
    )

    status = models.CharField(max_length=40)

    date_approved = models.DateTimeField(_('approved'), null=True, blank=True)
    date_started = models.DateTimeField(_('started'), null=True, blank=True)
    date_completed = models.DateTimeField(_('completed'), null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @classmethod
    def generate(cls, activity):
        from .states import GrantPayoutStateMachine
        for payout in cls.objects.filter(activity=activity):
            if payout.status == GrantPayoutStateMachine.new.value:
                payout.delete()
            elif payout.grants.count() == 0:
                raise AssertionError('Payout without donations already started!')
        ready_grants = activity.grants.filter(status='new', grantdonor__payout__isnull=True)
        groups = set([
            don.amount_currency for don in
            ready_grants
        ])
        for currency in groups:
            payout = cls.objects.create(
                activity=activity,
                currency=currency
            )
            for grant in ready_grants:
                grant.payout = payout
                grant.save()

    def transfer_to_account(self):
        stripe = get_stripe()
        connect_account_id = self.activity.payout_account.account_id

        total_amount = self.total_amount
        amount_in_cents = int(total_amount.amount * 100)
        transfer = stripe.Transfer.create(
            amount=amount_in_cents,
            currency=str(total_amount.currency).lower(),
            destination=connect_account_id,
            description=f"Grant payout for {self.activity.title}",
            metadata={
                "payout_id": str(self.id),
                "grant_application_id": str(self.activity.id),
                "grant_application_title": self.activity.title,
            },
        )
        return transfer

    @property
    def total_amount(self):
        if self.currency:
            return Money(self.grants.aggregate(total=Sum('amount'))['total'] or 0, self.currency)
        return self.grants.aggregate(total=Sum('amount'))['total']

    class Meta(object):
        verbose_name = _('Grant payout')
        verbose_name_plural = _('Grant payouts')

    def __str__(self):
        return '{} #{} {}'.format(_('Payout'), self.id, self.activity.title)


class GrantApplication(Activity):

    target = MoneyField(default=Money(0, 'EUR'), null=True, blank=True)

    impact_location = models.ForeignKey(
        'geo.Geolocation',
        null=True, blank=True,
        related_name='grant_applications',
        on_delete=models.SET_NULL
    )

    bank_account = models.ForeignKey('funding.BankAccount', null=True, blank=True, on_delete=SET_NULL)
    started = models.DateTimeField(
        _('started'),
        null=True,
        blank=True,
    )
    needs_review = True

    validators = [
        TargetValidator,
    ]

    activity_type = _('Grant application')

    @property
    def required_fields(self):
        fields = [
            "title",
            "description.html",
            "target",
        ]
        return fields

    @property
    def amount_granted(self):
        grants = self.contributors.instance_of(GrantDonor)
        amount = 0
        for grant in grants:
            amount += grant.amount.amount
        return Money(amount, self.target.currency)

    @property
    def payout_account(self):
        if self.bank_account:
            return self.bank_account.connect_account
        else:
            return self.owner.funding_payout_account.first()

    @property
    def grants(self):
        if self.pk:
            return self.contributors.instance_of(GrantDonor).all()
        else:
            return GrantDonor.objects.none()

    class JSONAPIMeta(object):
        resource_name = 'activities/grant-applications'

    class Meta(object):
        verbose_name = _("Grant application")
        verbose_name_plural = _("Grant applications")
        permissions = (
            ('api_read_grantapplication', 'Can view grant application through the API'),
            ('api_add_grantapplication', 'Can add funding through the API'),
            ('api_change_grantapplication', 'Can change funding through the API'),
            ('api_delete_grantapplication', 'Can delete funding through the API'),

            ('api_read_own_grantapplication', 'Can view own funding through the API'),
            ('api_add_own_grantapplication', 'Can add own funding through the API'),
            ('api_change_own_grantapplication', 'Can change own funding through the API'),
            ('api_delete_own_grantapplication', 'Can delete own funding through the API'),
        )

    @property
    def activity_date(self):
        return self.created.date()

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        return f"{domain}/{language}/activities/details/grant-application/{self.id}/{self.slug}"


class LedgerItemChoices(DjangoChoices):
    debit = ChoiceItem(
        'debit',
        label=_("Debit")
    )
    credit = ChoiceItem(
        'credit',
        label=_("credit")
    )


class GrantFund(models.Model):
    name = models.CharField(max_length=200)

    currency = models.CharField(max_length=10, default='EUR')

    description = QuillField(_("Description"), blank=True)
    organization = models.ForeignKey(
        'organizations.Organization',
        null=True, blank=True,
        on_delete=SET_NULL
    )

    grant_provider = models.ForeignKey(
        GrantProvider,
        null=True,
        blank=True,
        related_name="funds",
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _('Grant fund')
        verbose_name_plural = _('Grant funds')

    def __str__(self):
        return self.name or f'Grant fund #{self.pk}'

    def save(self, *args, **kwargs):
        if not self.currency:
            self.currency = properties.DEFAULT_CURRENCY

        super().save(*args, **kwargs)

    def credit_items(self, statuses=['final']):
        return self.ledger_items.filter(type=LedgerItemChoices.credit, status__in=statuses)

    def debit_items(self, statuses=['final']):
        return self.ledger_items.filter(type=LedgerItemChoices.debit, status__in=statuses)

    @property
    def total_credit(self):
        return self.credit_items().aggregate(total=Sum('amount'))['total'] or 0
    total_credit.fget.short_description = _('Total payed out')

    @property
    def total_debit(self):
        return self.debit_items().aggregate(total=Sum('amount'))['total'] or 0
    total_debit.fget.short_description = _('Total budget')

    @property
    def total_pending_credit(self):
        return self.credit_items(['pending', 'final']).aggregate(total=Sum('amount'))['total'] or 0

    @property
    def total_pending_debit(self):
        return self.debit_items(['pending', 'final']).aggregate(total=Sum('amount'))['total'] or 0

    @property
    def balance(self):
        return self.total_debit - self.total_credit
    balance.fget.short_description = _('Balance')

    @property
    def pending_balance(self):
        return self.total_pending_debit - self.total_pending_credit
    pending_balance.fget.short_description = _('Pending balance')

    class JSONAPIMeta(object):
        resource_name = "activities/grant-funds"


class LedgerItem(TriggerMixin, models.Model):
    status = models.CharField(max_length=40)

    amount = MoneyField()
    type = models.CharField(choices=LedgerItemChoices.choices)
    fund = models.ForeignKey(GrantFund, related_name='ledger_items', on_delete=models.CASCADE)

    object_type = models.ForeignKey(
        ContentType, related_name='ledger_item', on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('object_type', 'object_id')

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    def clean(self):
        if str(self.amount.currency) != self.fund.currency:
            raise ValidationError({'amount': _('Currency should match fund currency')})

        super().clean()


class GrantDonor(Contributor):
    amount = MoneyField()
    fund = models.ForeignKey(
        GrantFund,
        null=True, blank=True,
        related_name="grants",
        on_delete=models.CASCADE
    )

    ledger_items = GenericRelation(
        LedgerItem, object_id_field="object_id", content_type_field='object_type',
        related_name="grants",
        on_delete=models.SET_NULL
    )

    payout = models.ForeignKey(
        GrantPayout,
        null=True, blank=True,
        on_delete=SET_NULL,
        related_name='grants'
    )

    class Meta:
        verbose_name = _('Grant')
        verbose_name_plural = _('Grants')

    class JSONAPIMeta(object):
        resource_name = "contributors/grants"

    def clean(self):
        if str(self.amount.currency) != self.fund.currency:
            raise ValidationError({'amount': _('Currency should match fund currency')})

        if not self.pk and self.amount.amount > self.fund.balance:
            raise ValidationError({'amount': _('Insufficient funds')})

        super().clean()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.ledger_items.exists():
            self.ledger_item = LedgerItem.objects.create(
                fund=self.fund,
                amount=self.amount,
                object=self,
                type=LedgerItemChoices.credit
            )
            self.save()


class GrantDeposit(TriggerMixin, models.Model):
    status = models.CharField(max_length=40)
    amount = MoneyField()

    reference = models.CharField(max_length=255, blank=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    fund = models.ForeignKey(GrantFund, on_delete=models.CASCADE)
    ledger_items = GenericRelation(
        LedgerItem, object_id_field="object_id", content_type_field='object_type'
    )

    def clean(self):
        if str(self.amount.currency) != self.fund.currency:
            raise ValidationError({'amount': _('Currency should match fund currency')})

        super().clean()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
