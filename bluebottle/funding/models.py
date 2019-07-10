from django.db import models
from django.db.models.aggregates import Sum
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from moneyed import Money
from polymorphic.models import PolymorphicModel

from bluebottle.activities.models import Activity, Contribution
from bluebottle.files.fields import ImageField
from bluebottle.fsm import FSMField, TransitionNotPossible, TransitionManager, TransitionsMixin
from bluebottle.funding.transitions import (
    FundingTransitions,
    DonationTransitions,
    PaymentTransitions
)
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import MoneyField


class Funding(Activity):
    deadline = models.DateField(_('deadline'), null=True, blank=True)
    duration = models.PositiveIntegerField(_('duration'), null=True, blank=True)

    target = MoneyField(null=True, blank=True)
    account = models.ForeignKey('payouts.PayoutAccount', null=True)
    transitions = TransitionManager(FundingTransitions, 'status')

    country = models.ForeignKey('geo.Country', null=True, blank=True)

    class JSONAPIMeta:
        resource_name = 'activities/funding'

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

    def save(self, *args, **kwargs):
        if self.status == FundingTransitions.values.draft:
            try:
                self.transitions.open()
            except TransitionNotPossible:
                pass

        super(Funding, self).save(*args, **kwargs)

    @property
    def amount_raised(self):
        """
        The sum of all contributions (donations) converted to the targets currency
        """
        totals = self.contributions.filter(
            status='success'
        ).values(
            'donation__amount_currency'
        ).annotate(
            total=Sum('donation__amount')
        )
        amounts = [Money(total['total'], total['donation__amount_currency']) for total in totals]
        amounts = [convert(amount, self.target.currency) for amount in amounts]

        return sum(amounts) or Money(0, self.target.currency)

    @property
    def payment_methods(self):
        methods = []
        if not self.target.currency:
            return []
        for provider in PaymentProvider.objects.all():
            for method in provider.payment_methods:
                if str(self.target.currency) in method.currencies:
                    methods.append(method)
        return methods


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
            status=DonationTransitions.values.success
        ).count()

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['-activity__created', 'amount']
        verbose_name = _("Gift")
        verbose_name_plural = _("Gifts")

    def delete(self, *args, **kwargs):
        if self.count:
            raise ValueError(_('Not allowed to delete a reward with successful donations.'))

        return super(Reward, self).delete(*args, **kwargs)


class BudgetLine(models.Model):
    """
    BudgetLine: Entries to the Activity Budget sheet.
    """
    activity = models.ForeignKey('funding.Funding', related_name='budgetlines')
    description = models.CharField(_('description'), max_length=255, default='')

    amount = MoneyField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

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
    deadline = models.DateField(_('deadline'), null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.title

    @property
    def amount_donated(self):
        donations = self.donations.filter(
            status=[DonationTransitions.values.success]
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
    reward = models.ForeignKey(Reward, null=True, related_name="donations")
    fundraiser = models.ForeignKey(Fundraiser, null=True, related_name="donations")

    transitions = TransitionManager(DonationTransitions, 'status')

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
        resource_name = 'funding/payment-methods'


class PaymentProvider(PolymorphicModel):

    public_settings = {}
    private_settings = {}

    currencies = []
    countries = []

    @property
    def payment_methods(self):
        return []

    def __unicode__(self):
        return str(self.polymorphic_ctype)
