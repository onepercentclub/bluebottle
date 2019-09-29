import random
import string

from babel.numbers import get_currency_name
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
from bluebottle.files.fields import ImageField
from bluebottle.fsm import FSMField, TransitionManager, TransitionsMixin
from bluebottle.funding.transitions import (
    FundingTransitions,
    DonationTransitions,
    PaymentTransitions,
    PayoutAccountTransitions
)
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import MoneyField, PrivateFileField
from bluebottle.utils.models import Validator, ValidatedModelMixin
from bluebottle.utils.utils import reverse_signed


class PaymentProvider(PolymorphicModel):

    public_settings = {}
    private_settings = {}

    currencies = []
    countries = []

    @classmethod
    def get_currency_choices(cls):
        currencies = []
        if isinstance(connection.tenant, FakeTenant):
            currencies = [('EUR', 'Euro')]
        else:
            for provider in cls.objects.all():
                for method in provider.payment_methods:
                    currencies += [(cur, get_currency_name(cur)) for cur in method.currencies]

        return list(set(currencies))

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


class BankPaymentProvider(PaymentProvider):
    currencies = ['EUR', 'USD', 'XOF', 'NGN', 'CFA', 'KES']


class KYCPassedValidator(Validator):
    code = 'kyc'
    message = _('Make sure your account is verified')
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

    @cached_property
    def amount_donated(self):
        """
        The sum of all contributions (donations) converted to the targets currency
        """
        totals = self.contributions.filter(
            status=FundingTransitions.values.succeeded
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
        return self.amount_donated + convert(
            self.amount_matching or Money(0, self.target.currency),
            self.target.currency
        )

    @property
    def payment_methods(self):
        if not self.bank_account or not self.bank_account.payment_methods:
            return []
        return self.bank_account.payment_methods

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


class Donation(Contribution):
    amount = MoneyField()
    payout_amount = MoneyField()
    client_secret = models.CharField(max_length=32, blank=True, null=True)
    reward = models.ForeignKey(Reward, null=True, related_name="donations")
    fundraiser = models.ForeignKey(Fundraiser, null=True, related_name="donations")
    name = models.CharField(max_length=200, null=True, blank=True,
                            verbose_name=_('Override donor name / Name for guest donation'))
    anonymous = models.BooleanField(_('anonymous'), default=False)

    transitions = TransitionManager(DonationTransitions, 'status')

    def save(self, *args, **kwargs):
        if not self.user and not self.client_secret:
            self.client_secret = ''.join(random.choice(string.ascii_lowercase) for i in range(32))

        if not self.payout_amount or (
                self.payout_amount.currency == self.amount.currency and
                self.payout_amount.amount != self.amount.amount):
            self.payout_amount = self.amount
        super(Donation, self).save(*args, **kwargs)

    @property
    def payment_method(self):
        if not self.payment:
            return None
        return self.payment.type

    class Meta:
        verbose_name = _('donation')
        verbose_name_plural = _('donations')

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

    owner = models.OneToOneField(
        'members.Member',
        related_name='funding_payout_account'
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    reviewed = models.BooleanField(default=False)

    transitions = TransitionManager(PayoutAccountTransitions, 'status')


class PlainPayoutAccount(PayoutAccount):
    document = PrivateFileField(
        max_length=110,
        upload_to='funding/documents'
    )

    ip_address = models.GenericIPAddressField(_('IP address'), blank=True, null=True, default=None)

    class Meta:
        verbose_name = _('payout document')
        verbose_name_plural = _('payout documents')

    @property
    def document_url(self):
        # pk may be unset if not saved yet, in which case no url can be
        # generated.
        if self.pk is not None and self.file:
            return reverse_signed('payout-document-file', args=(self.pk,))
        return None


class BankAccount(PolymorphicModel):
    owner = models.OneToOneField(
        'members.Member',
        related_name='funding_bank_account',
        null=True,
        blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    reviewed = models.BooleanField(default=False)

    @property
    def verified(self):
        return self.reviewed

    provider_class = None

    @property
    def funding(self):
        return self.funding_set.order_by('-created').first()

    @property
    def payment_methods(self):
        provider = self.provider_class.objects.get()
        return provider.payment_methods


class PlainBankAccount(BankAccount):

    provider_class = BankPaymentProvider

    account_number = models.CharField(
        _("bank account number"), max_length=100, null=True, blank=True)
    account_holder_name = models.CharField(
        _("account holder name"), max_length=100, null=True, blank=True)
    account_holder_address = models.CharField(
        _("account holder address"), max_length=500, null=True, blank=True)
    account_bank_country = models.CharField(
        _("bank country"), max_length=100, null=True, blank=True)
    account_details = models.CharField(
        _("account details"), max_length=500, null=True, blank=True)
