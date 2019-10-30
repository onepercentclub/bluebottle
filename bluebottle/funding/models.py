# -*- coding: utf-8 -*-
import random
import string
from itertools import groupby

from babel.numbers import get_currency_name
from django.core.cache import cache
from django.db import connection
from django.db import models
from django.db.models import SET_NULL
from django.db.models.aggregates import Sum
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from moneyed import Money
from polymorphic.models import PolymorphicModel
from tenant_schemas.postgresql_backend.base import FakeTenant

from bluebottle.activities.models import Activity, Contribution
from bluebottle.files.fields import ImageField, DocumentField
from bluebottle.fsm import FSMField, TransitionManager, TransitionsMixin
from bluebottle.funding.transitions import (
    FundingTransitions,
    DonationTransitions,
    PaymentTransitions,
    PayoutAccountTransitions,
    PlainPayoutAccountTransitions,
    PayoutTransitions)
from bluebottle.payouts_dorado.adapters import DoradoPayoutAdapter
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import MoneyField
from bluebottle.utils.models import Validator, ValidatedModelMixin


class PaymentCurrency(models.Model):

    provider = models.ForeignKey('funding.PaymentProvider')
    code = models.CharField(max_length=3, default='EUR')
    min_amount = models.DecimalField(default=5.0, decimal_places=2, max_digits=10)
    max_amount = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=10)

    default1 = models.DecimalField(decimal_places=2, max_digits=10)
    default2 = models.DecimalField(decimal_places=2, max_digits=10)
    default3 = models.DecimalField(decimal_places=2, max_digits=10)
    default4 = models.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        verbose_name = _('Payment currency')
        verbose_name_plural = _('Payment currencies')


class PaymentProvider(PolymorphicModel):

    public_settings = {}
    private_settings = {}

    @property
    def available_currencies(self):
        currencies = []
        for method in self.payment_methods:
            for cur in method.currencies:
                if cur not in currencies:
                    currencies.append(cur)
        return currencies

    @classmethod
    def get_currency_choices(cls):
        currencies = []
        if isinstance(connection.tenant, FakeTenant):
            currencies = [('EUR', 'Euro')]
        else:
            for provider in cls.objects.all():
                for cur in provider.paymentcurrency_set.all():
                    currency = (cur.code, get_currency_name(cur.code))
                    if currency not in currencies:
                        currencies.append(currency)
        return currencies

    @classmethod
    def get_default_currency(cls):
        if len(cls.get_currency_choices()):
            return cls.get_currency_choices()[0]
        return 'EUR'

    @property
    def payment_methods(self):
        return []

    def __unicode__(self):
        return str(self.polymorphic_ctype)

    @property
    def name(self):
        return self.__class__.__name__.replace('PaymentProvider', '').lower()

    def save(self, **kwargs):
        created = False
        if self.pk is None:
            created = True
        model = super(PaymentProvider, self).save(**kwargs)
        if created:
            for currency in self.available_currencies:
                PaymentCurrency.objects.create(
                    provider=self,
                    code=currency,
                    min_amount=5,
                    default1=10,
                    default2=20,
                    default3=50,
                    default4=100,
                )
        return model


class KYCPassedValidator(Validator):
    code = 'kyc'
    message = [_('Make sure your account is verified')]
    field = 'kyc'

    def is_valid(self):
        return self.instance.bank_account and self.instance.bank_account.verified


class Funding(Activity):
    deadline = models.DateTimeField(_('deadline'), null=True, blank=True)
    duration = models.PositiveIntegerField(_('duration'), null=True, blank=True)

    target = MoneyField(default=Money(0, 'EUR'), null=True, blank=True)
    amount_matching = MoneyField(default=Money(0, 'EUR'), null=True, blank=True)
    country = models.ForeignKey('geo.Country', null=True, blank=True)
    bank_account = models.ForeignKey('funding.BankAccount', null=True, blank=True, on_delete=SET_NULL)
    transitions = TransitionManager(FundingTransitions, 'status')

    needs_review = True

    validators = [KYCPassedValidator]

    @property
    def required_fields(self):
        fields = ['title', 'description', 'target', 'bank_account', 'budget_lines']

        if not self.duration:
            fields.append('deadline')

        return fields

    class JSONAPIMeta:
        resource_name = 'activities/fundings'

    class Meta:
        verbose_name = _("Funding")
        verbose_name_plural = _("Funding Activities")
        permissions = (
            ('api_read_funding', 'Can view funding through the API'),
            ('api_add_funding', 'Can add funding through the API'),
            ('api_change_funding', 'Can change funding through the API'),
            ('api_delete_funding', 'Can delete funding through the API'),

            ('api_read_own_funding', 'Can view own funding through the API'),
            ('api_add_own_funding', 'Can add own funding through the API'),
            ('api_change_own_funding', 'Can change own funding through the API'),
            ('api_delete_own_funding', 'Can delete own funding through the API'),
        )

    def update_amounts(self):
        cache_key = '{}.{}.amount_donated'.format(connection.tenant.schema_name, self.id)
        cache.delete(cache_key)
        return self.amount_donated

    @property
    def amount_donated(self):
        """
        The sum of all contributions (donations) converted to the targets currency
        """
        cache_key = '{}.{}.amount_donated'.format(connection.tenant.schema_name, self.id)
        total = cache.get(cache_key)
        if not total:
            totals = self.contributions.filter(
                status=FundingTransitions.values.succeeded
            ).values(
                'donation__amount_currency'
            ).annotate(
                total=Sum('donation__amount')
            )
            amounts = [Money(tot['total'], tot['donation__amount_currency']) for tot in totals]
            amounts = [convert(amount, self.target.currency) for amount in amounts]
            if self.target:
                total = sum(amounts) or Money(0, self.target.currency)
            else:
                total = Money(0, 'EUR')
            cache.set(cache_key, total)
        return total

    @property
    def genuine_amount_donated(self):
        """
        The sum of all contributions (donations) without pledges converted to the targets currency
        """
        totals = self.contributions.filter(
            status=FundingTransitions.values.succeeded,
            donation__payment__pledgepayment__isnull=True
        ).values(
            'donation__amount_currency'
        ).annotate(
            total=Sum('donation__amount')
        )
        amounts = [Money(total['total'], total['donation__amount_currency']) for total in totals]
        amounts = [convert(amount, self.target.currency) for amount in amounts]

        return sum(amounts) or Money(0, self.target.currency)

    @cached_property
    def amount_pledged(self):
        """
        The sum of all contributions (donations) converted to the targets currency
        """
        totals = self.contributions.filter(
            status=FundingTransitions.values.succeeded,
            donation__payment__pledgepayment__isnull=False
        ).values(
            'donation__amount_currency'
        ).annotate(
            total=Sum('donation__amount')
        )
        amounts = [Money(total['total'], total['donation__amount_currency']) for total in totals]
        amounts = [convert(amount, self.target.currency) for amount in amounts]

        return sum(amounts) or Money(0, self.target.currency)

    @property
    def amount_raised(self):
        """
        The sum of amount donated + amount matching
        """
        if self.target:
            currency = self.target.currency
        else:
            currency = 'EUR'
        total = self.amount_donated
        if self.amount_matching:
            total += convert(
                self.amount_matching,
                currency
            )
        return total

    def save(self, *args, **kwargs):
        for reward in self.rewards.all():
            if not reward.amount.currency == self.target.currency:
                reward.amount = Money(reward.amount.amount, self.target.currency)
                reward.save()

        for line in self.budget_lines.all():
            if not line.amount.currency == self.target.currency:
                line.amount = Money(line.amount.amount, self.target.currency)
                line.save()

        super(Funding, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.title or str(_('-empty-'))


class Reward(models.Model):
    """
    Rewards for donations
    """
    amount = MoneyField(_('Amount'))
    title = models.CharField(_('Title'), max_length=200)
    description = models.CharField(_('Description'), max_length=500)
    activity = models.ForeignKey('funding.Funding', verbose_name=_('Activity'), related_name='rewards')
    limit = models.IntegerField(
        _('Limit'),
        null=True,
        blank=True,
        help_text=_('How many of this rewards are available')
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def count(self):
        return self.donations.filter(
            status=DonationTransitions.values.succeeded
        ).count()

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['-activity__created', 'amount']
        verbose_name = _("Gift")
        verbose_name_plural = _("Gifts")

    class JSONAPIMeta:
        resource_name = 'activities/rewards'

    def delete(self, *args, **kwargs):
        if self.count:
            raise ValueError(_('Not allowed to delete a reward with successful donations.'))

        return super(Reward, self).delete(*args, **kwargs)


class BudgetLine(models.Model):
    """
    BudgetLine: Entries to the Activity Budget sheet.
    """
    activity = models.ForeignKey('funding.Funding', related_name='budget_lines')
    description = models.CharField(_('description'), max_length=255, default='')

    amount = MoneyField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class JSONAPIMeta:
        resource_name = 'activities/budget-lines'

    class Meta:
        verbose_name = _('budget line')
        verbose_name_plural = _('budget lines')

    def __unicode__(self):
        return u'{0} - {1}'.format(self.description, self.amount)


class Fundraiser(models.Model):
    owner = models.ForeignKey('members.Member', related_name="funding_fundraisers")
    activity = models.ForeignKey(
        'funding.Funding',
        verbose_name=_("activity"),
        related_name="fundraisers"
    )

    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)

    image = ImageField(blank=True, null=True)

    amount = MoneyField(_("amount"))
    deadline = models.DateTimeField(_('deadline'), null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.title

    @cached_property
    def amount_donated(self):
        donations = self.donations.filter(
            status=[DonationTransitions.values.succeeded]
        )

        totals = [
            Money(data['amount__sum'], data['amount_currency']) for data in
            donations.values('amount_currency').annotate(Sum('amount')).order_by()
        ]

        totals = [convert(amount, self.amount.currency) for amount in totals]

        return sum(totals) or Money(0, self.amount.currency)

    class Meta():
        verbose_name = _('fundraiser')
        verbose_name_plural = _('fundraisers')


class Payout(TransitionsMixin, models.Model):
    activity = models.ForeignKey(
        'funding.Funding',
        verbose_name=_("activity"),
        related_name="payouts"
    )
    provider = models.CharField(max_length=100)
    currency = models.CharField(max_length=5)

    status = FSMField(
        default=PayoutTransitions.values.new,
    )
    transitions = TransitionManager(PayoutTransitions, 'status')

    date_approved = models.DateTimeField(_('approved'), null=True, blank=True)
    date_started = models.DateTimeField(_('started'), null=True, blank=True)
    date_completed = models.DateTimeField(_('completed'), null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @classmethod
    def generate(cls, activity):
        for (currency, provider), donations in groupby(
            activity.contributions.filter(status='succeeded'),
            lambda x: (x.amount_currency, x.payment.provider)
        ):
            payout = cls.objects.create(
                activity=activity,
                provider=provider,
                currency=currency
            )
            for donation in donations:
                donation.payout = payout
                donation.save()

    @property
    def total_amount(self):
        if self.currency:
            return Money(self.donations.aggregate(total=Sum('amount'))['total'] or 0, self.currency)

    class Meta():
        verbose_name = _('payout')
        verbose_name_plural = _('payout')


class Donation(Contribution):
    amount = MoneyField()
    client_secret = models.CharField(max_length=32, blank=True, null=True)
    reward = models.ForeignKey(Reward, null=True, related_name="donations")
    fundraiser = models.ForeignKey(Fundraiser, null=True, related_name="donations")
    name = models.CharField(max_length=200, null=True, blank=True,
                            verbose_name=_('Override donor name / Name for guest donation'))
    anonymous = models.BooleanField(_('anonymous'), default=False)
    payout = models.ForeignKey('funding.Payout', null=True, blank=True, on_delete=SET_NULL, related_name='donations')

    transitions = TransitionManager(DonationTransitions, 'status')

    def save(self, *args, **kwargs):
        if not self.user and not self.client_secret:
            self.client_secret = ''.join(random.choice(string.ascii_lowercase) for i in range(32))

        super(Donation, self).save(*args, **kwargs)

    @property
    def payment_method(self):
        if not self.payment:
            return None
        return self.payment.type

    class Meta:
        verbose_name = _('Donation')
        verbose_name_plural = _('Donations')

    def __unicode__(self):
        return u'{}'.format(self.amount)

    class JSONAPIMeta:
        resource_name = 'contributions/donations'


class Payment(TransitionsMixin, PolymorphicModel):
    status = FSMField(
        default=PaymentTransitions.values.new,
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    donation = models.OneToOneField(Donation, related_name='payment')

    @property
    def can_update(self):
        return hasattr(self, 'update')

    def __unicode__(self):
        return "{} - {}".format(self.polymorphic_ctype, self.id)

    class Meta:
        permissions = (
            ('refund_payment', 'Can refund payments'),
        )


class LegacyPayment(Payment):
    method = models.CharField(max_length=100)
    data = models.TextField()

    transitions = TransitionManager(PaymentTransitions, 'status')


class PaymentMethod(object):
    code = ''
    provider = ''
    name = ''
    currencies = []
    countries = []

    def __init__(self, provider, code, name=None, currencies=None, countries=None):
        self.provider = provider
        self.code = code
        if name:
            self.name = name
        else:
            self.name = code
        if currencies:
            self.currencies = currencies
        if countries:
            self.countries = countries

    @property
    def id(self):
        return format_html("{}-{}", self.provider, self.code)

    @property
    def pk(self):
        return self.id

    class JSONAPIMeta:
        resource_name = 'payments/payment-methods'


class PayoutAccount(ValidatedModelMixin, PolymorphicModel, TransitionsMixin):
    status = FSMField(
        default=PayoutAccountTransitions.values.new
    )

    owner = models.ForeignKey(
        'members.Member',
        related_name='funding_payout_account'
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    reviewed = models.BooleanField(default=False)

    def send_payout(self):
        adapter = DoradoPayoutAdapter(self.activity)
        adapter.trigger_payout()


class PlainPayoutAccount(PayoutAccount):
    document = DocumentField(blank=True, null=True)

    ip_address = models.GenericIPAddressField(_('IP address'), blank=True, null=True, default=None)

    transitions = TransitionManager(PlainPayoutAccountTransitions, 'status')

    class Meta:
        verbose_name = _('plain payout account')
        verbose_name_plural = _('plain payout accounts')

    class JSONAPIMeta:
        resource_name = 'payout-accounts/plains'

    @property
    def required_fields(self):
        required = []
        if self.status == 'new':
            required.append('document')
        return required


class BankAccount(PolymorphicModel):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    reviewed = models.BooleanField(default=False)

    connect_account = models.ForeignKey(
        'funding.PayoutAccount',
        null=True, blank=True,
        related_name='external_accounts')

    @property
    def parent(self):
        return self.connect_account

    @property
    def verified(self):
        return self.reviewed

    @property
    def owner(self):
        return self.connect_account.owner

    provider_class = None

    @property
    def type(self):
        return self.provider_class().name

    @property
    def funding(self):
        return self.funding_set.order_by('-created').first()

    @property
    def payment_methods(self):
        provider = self.provider_class.objects.get()
        return provider.payment_methods

    class JSONAPIMeta:
        resource_name = 'payout-accounts/external-accounts'

    public_data = {}
