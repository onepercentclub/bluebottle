# -*- coding: utf-8 -*-
import logging
import random
import string
from builtins import object
from builtins import range

from babel.numbers import get_currency_name
from django.core.exceptions import ValidationError
from django.db import connection
from django.db import models
from django.db.models import Count
from django.db.models import SET_NULL
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from future.utils import python_2_unicode_compatible
from moneyed import Money
from polymorphic.models import PolymorphicModel
from tenant_schemas.postgresql_backend.base import FakeTenant

from bluebottle.activities.models import Activity, Contributor
from bluebottle.activities.models import Contribution
from bluebottle.clients import properties
from bluebottle.files.fields import ImageField, PrivateDocumentField
from bluebottle.fsm.triggers import TriggerMixin
from bluebottle.funding.validators import (
    DeadlineValidator,
    TargetValidator,
    DeadlineMaxValidator,
    BudgetLineValidator,
    KYCReadyValidator,
)
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import MoneyField
from bluebottle.utils.models import BasePlatformSettings, AnonymizationMixin, ValidatedModelMixin

logger = logging.getLogger(__name__)


class PaymentCurrency(models.Model):

    provider = models.ForeignKey('funding.PaymentProvider', on_delete=models.CASCADE)
    code = models.CharField(max_length=3, default='EUR')
    min_amount = models.DecimalField(default=5.0, decimal_places=2, max_digits=10)
    max_amount = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=10)

    default1 = models.DecimalField(decimal_places=2, max_digits=10)
    default2 = models.DecimalField(decimal_places=2, max_digits=10)
    default3 = models.DecimalField(decimal_places=2, max_digits=10)
    default4 = models.DecimalField(decimal_places=2, max_digits=10)

    class Meta(object):
        verbose_name = _('Payment currency')
        verbose_name_plural = _('Payment currencies')


@python_2_unicode_compatible
class PaymentProvider(PolymorphicModel):

    title = 'Payment Service Provider'
    provider = 'default'

    public_settings = {}
    private_settings = {}

    refund_enabled = False

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

    def __str__(self):
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


class Funding(Activity):

    deadline = models.DateTimeField(
        _('deadline'),
        null=True,
        blank=True,
        help_text=_('If you enter a deadline, leave the duration field empty. This will override the duration.')
    )

    duration = models.PositiveIntegerField(
        _('duration'),
        null=True,
        blank=True,
        help_text=_('If you enter a duration, leave the deadline field empty for it to be automatically calculated.')
    )

    target = MoneyField(default=Money(0, 'EUR'), null=True, blank=True)
    amount_matching = MoneyField(default=Money(0, 'EUR'), null=True, blank=True)
    amount_donated = MoneyField(default=Money(0, 'EUR'), null=True, blank=True)
    amount_pledged = MoneyField(default=Money(0, 'EUR'), null=True, blank=True)

    country = models.ForeignKey('geo.Country', null=True, blank=True, on_delete=models.SET_NULL)
    bank_account = models.ForeignKey('funding.BankAccount', null=True, blank=True, on_delete=SET_NULL)
    started = models.DateTimeField(
        _('started'),
        null=True,
        blank=True,
    )

    needs_review = True

    validators = [
        DeadlineValidator,
        DeadlineMaxValidator,
        TargetValidator,
        BudgetLineValidator,
        KYCReadyValidator,
    ]

    auto_approve = False

    activity_type = _('Crowdfunding campaign')

    def admin_clean(self):
        for val in self.validators:
            validator = val(self)
            if not validator.is_valid():
                raise ValidationError(validator.message)

    @property
    def required_fields(self):
        fields = super().required_fields + [
            "title",
            "description",
            "target",
            "bank_account",
        ]

        if not self.duration:
            fields.append('deadline')

        return fields

    class JSONAPIMeta(object):
        resource_name = 'activities/fundings'

    class Meta(object):
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
        from bluebottle.funding.utils import calculate_total
        from .states import DonorStateMachine

        if not self.has_deleted_data:
            donations = self.donations.filter(
                status__in=(
                    DonorStateMachine.succeeded.value,
                    DonorStateMachine.activity_refunded.value,
                )
            )
            currency = self.target.currency if self.target else properties.DEFAULT_CURRENCY

            self.amount_donated = calculate_total(donations, currency)
            self.amount_pledged = calculate_total(
                donations.filter(
                    donor__payment__pledgepayment__isnull=False
                ),
                currency
            )
            self.save()

    @property
    def total_budget(self):
        budget_lines = self.budget_lines.all()
        total_amount = sum(line.amount.amount for line in budget_lines)
        return Money(currency=self.target.currency, amount=total_amount)

    @property
    def activity_date(self):
        return self.deadline

    @property
    def donations(self):
        return self.contributors.instance_of(Donor)

    @property
    def succeeded_contributor_count(self):
        return self.donations.filter(status='succeeded').count()

    @property
    def genuine_amount_donated(self):
        """
        The sum of all contributors (donations) without pledges converted to the targets currency
        """
        return self.amount_donated - self.amount_pledged

    @property
    def amount_raised(self):
        """
        The sum of amount donated + amount matching
        """
        if self.target:
            currency = self.target.currency
        else:
            currency = 'EUR'
        total = convert(self.amount_donated, currency)
        if self.amount_matching:
            total += convert(
                self.amount_matching,
                currency
            )
        return total

    @property
    def payout_account(self):
        if self.bank_account:
            return self.bank_account.connect_account
        else:
            return self.owner.funding_payout_account.first()

    @property
    def stats(self):
        from .states import DonorStateMachine
        stats = self.donations.filter(
            status=DonorStateMachine.succeeded.value
        ).aggregate(
            count=Count('user__id')
        )
        stats['amount'] = {'amount': self.amount_raised.amount, 'currency': str(self.amount_raised.currency)}
        return stats

    def save(self, *args, **kwargs):
        if self.target:
            for reward in self.rewards.all():
                if reward.amount and not reward.amount.currency == self.target.currency:
                    reward.amount = Money(reward.amount.amount, self.target.currency)
                    reward.save()

            for line in self.budget_lines.all():
                if self.target and not line.amount.currency == self.target.currency:
                    line.amount = Money(line.amount.amount, self.target.currency)
                    line.save()

        super(Funding, self).save(*args, **kwargs)


@python_2_unicode_compatible
class Reward(models.Model):
    """
    Rewards for donations
    """
    amount = MoneyField(_('Amount'))
    title = models.CharField(_('Title'), max_length=200)
    description = models.CharField(_('Description'), max_length=500, null=True, blank=True)
    activity = models.ForeignKey(
        'funding.Funding', verbose_name=_('Activity'), related_name='rewards', on_delete=models.CASCADE
    )
    limit = models.IntegerField(
        _('Limit'),
        null=True,
        blank=True,
        help_text=_('How many of this rewards are available')
    )

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    @property
    def count(self):
        from .states import DonorStateMachine
        return self.donations.filter(
            status=DonorStateMachine.succeeded.value
        ).count()

    def __str__(self):
        return self.title

    class Meta(object):
        ordering = ['-activity__created', 'amount']
        verbose_name = _("Gift")
        verbose_name_plural = _("Gifts")

    class JSONAPIMeta(object):
        resource_name = 'activities/rewards'

    def delete(self, *args, **kwargs):
        if self.count:
            raise ValueError(_('Not allowed to delete a reward with successful donations.'))

        return super(Reward, self).delete(*args, **kwargs)


@python_2_unicode_compatible
class BudgetLine(models.Model):
    """
    BudgetLine: Entries to the Activity Budget sheet.
    """
    activity = models.ForeignKey(
        'funding.Funding', related_name='budget_lines', on_delete=models.CASCADE
    )
    description = models.CharField(_('description'), max_length=255, default='')

    amount = MoneyField()

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class JSONAPIMeta(object):
        resource_name = 'activities/budget-lines'

    class Meta(object):
        verbose_name = _('budget line')
        verbose_name_plural = _('budget lines')

    def __str__(self):
        return u'{0} - {1}'.format(self.description, self.amount)


@python_2_unicode_compatible
class Fundraiser(AnonymizationMixin, models.Model):
    owner = models.ForeignKey(
        'members.Member', related_name="funding_fundraisers", on_delete=models.CASCADE
    )
    activity = models.ForeignKey(
        'funding.Funding',
        verbose_name=_("activity"),
        related_name="fundraisers",
        on_delete=models.CASCADE
    )

    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)

    image = ImageField(blank=True, null=True)

    amount = MoneyField(_("amount"))
    deadline = models.DateTimeField(_('deadline'), null=True, blank=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @cached_property
    def amount_donated(self):
        from .states import DonorStateMachine
        donations = self.donations.filter(
            status__in=[
                DonorStateMachine.succeeded.value,
                DonorStateMachine.activity_refunded.value,
            ]
        )

        totals = [
            Money(data['amount__sum'], data['amount_currency']) for data in
            donations.values('amount_currency').annotate(Sum('amount')).order_by()
        ]

        totals = [convert(amount, self.amount.currency) for amount in totals]

        return sum(totals) or Money(0, self.amount.currency)

    class Meta(object):
        verbose_name = _('fundraiser')
        verbose_name_plural = _('fundraisers')


@python_2_unicode_compatible
class Payout(TriggerMixin, models.Model):
    activity = models.ForeignKey(
        'funding.Funding',
        verbose_name=_("activity"),
        related_name="payouts",
        on_delete=models.CASCADE
    )
    provider = models.CharField(max_length=100)
    currency = models.CharField(max_length=5)

    status = models.CharField(max_length=40)

    date_approved = models.DateTimeField(_('approved'), null=True, blank=True)
    date_started = models.DateTimeField(_('started'), null=True, blank=True)
    date_completed = models.DateTimeField(_('completed'), null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @classmethod
    def generate(cls, activity):
        from .states import PayoutStateMachine
        for payout in cls.objects.filter(activity=activity):
            if payout.status == PayoutStateMachine.new.value:
                payout.delete()
            elif payout.donations.count() == 0:
                raise AssertionError('Payout without donations already started!')
        ready_donations = activity.donations.filter(status='succeeded', donor__payout__isnull=True)
        groups = set([
            (don.payout_amount_currency, don.payment.provider) for don in
            ready_donations
        ])
        for currency, provider in groups:
            donations = [
                don for don in
                ready_donations.filter(donor__payout_amount_currency=currency)
                if don.payment.provider == provider
            ]
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
            return Money(self.donations.aggregate(total=Sum('payout_amount'))['total'] or 0, self.currency)
        return self.donations.aggregate(total=Sum('amount'))['total']

    class Meta(object):
        verbose_name = _('payout')
        verbose_name_plural = _('payouts')

    def __str__(self):
        return '{} #{} {}'.format(_('Payout'), self.id, self.activity.title)


@python_2_unicode_compatible
class Donor(Contributor):
    amount = MoneyField()
    payout_amount = MoneyField()
    client_secret = models.CharField(max_length=32, blank=True, null=True)
    reward = models.ForeignKey(
        Reward, null=True, blank=True, related_name="donations", on_delete=models.CASCADE
    )
    fundraiser = models.ForeignKey(
        Fundraiser, null=True, blank=True, related_name="donations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200, null=True, blank=True,
                            verbose_name=_('Fake name'),
                            help_text=_('Override donor name / Name for guest donation'))
    anonymous = models.BooleanField(_('anonymous'), default=False)
    payout = models.ForeignKey(
        'funding.Payout', null=True, blank=True, on_delete=SET_NULL, related_name='donations'
    )

    def save(self, *args, **kwargs):
        if not self.user and not self.client_secret:
            self.client_secret = ''.join(random.choice(string.ascii_lowercase) for i in range(32))

        if not self.payout_amount:
            self.payout_amount = self.amount

        super(Donor, self).save(*args, **kwargs)

    @property
    def date(self):
        return self.created

    @property
    def available_payment_methods(self):
        payment_methods = self.activity.bank_account.payment_methods
        return payment_methods

    @property
    def payment_method(self):
        if not self.payment:
            return None
        return self.payment.type

    class Meta(object):
        verbose_name = _('Donation')
        verbose_name_plural = _('Donations')

    class JSONAPIMeta(object):
        resource_name = 'contributors/donations'


@python_2_unicode_compatible
class MoneyContribution(Contribution):

    value = MoneyField()

    class Meta(object):
        verbose_name = _('Donation')
        verbose_name_plural = _('Contributions')


@python_2_unicode_compatible
class Payment(TriggerMixin, PolymorphicModel):
    status = models.CharField(max_length=40)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField()

    donation = models.OneToOneField(Donor, related_name='payment', on_delete=models.CASCADE)

    @property
    def can_update(self):
        return hasattr(self, 'update')

    @property
    def can_refund(self):
        return hasattr(self, 'refund')

    def save(self, *args, **kwargs):
        self.updated = timezone.now()

        super(Payment, self).save(*args, **kwargs)

    def __str__(self):
        return "{} - {}".format(self.polymorphic_ctype, self.id)

    class Meta(object):
        permissions = (
            ('refund_payment', 'Can refund payments'),
        )


class LegacyPayment(Payment):
    method = models.CharField(max_length=100)
    data = models.TextField()

    provider = 'legacy'


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
        return "{}-{}".format(self.provider, self.code)

    @property
    def pk(self):
        return self.id

    class JSONAPIMeta(object):
        resource_name = 'payments/payment-methods'


@python_2_unicode_compatible
class PayoutAccount(TriggerMixin, ValidatedModelMixin, AnonymizationMixin, PolymorphicModel):
    status = models.CharField(max_length=40)

    owner = models.ForeignKey(
        'members.Member',
        related_name='funding_payout_account',
        on_delete=models.CASCADE
    )

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    reviewed = models.BooleanField(default=False)

    public = models.BooleanField(
        _('Public payout account'),
        default=False,
        help_text=_((
            "Allow users to choose this payout account when setting up a "
            "crowdfunding campaign (only applies if crowdfunding for public "
            "payout accounts is enabled)."
        ))
    )

    partner_organization = models.ForeignKey(
        'organizations.Organization',
        blank=True, null=True,
        related_name='payout_accounts',
        verbose_name=_('Partner organisation'),
        on_delete=models.SET_NULL
    )

    @property
    def funding(self):
        for account in self.external_accounts.all():
            for funding in account.funding_set.all():
                return funding

    def __str__(self):
        return "Payout account #{}".format(self.id)


class PlainPayoutAccount(PayoutAccount):
    document = PrivateDocumentField(
        blank=True, null=True, on_delete=models.deletion.SET_NULL, view_name='kyc-document'
    )

    ip_address = models.GenericIPAddressField(_('IP address'), blank=True, null=True, default=None)

    @property
    def verified(self):
        return self.reviewed

    class Meta(object):
        verbose_name = _('Plain KYC account')
        verbose_name_plural = _('Plain KYC accounts')

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/plains'

    @property
    def required_fields(self):
        required = []
        if self.status == 'new':
            required.append('document')
        return required

    def __str__(self):
        return "KYC account for {}".format(self.owner.full_name)


@python_2_unicode_compatible
class BankAccount(TriggerMixin, PolymorphicModel):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    reviewed = models.BooleanField(default=False)

    provider = 'default'

    connect_account = models.ForeignKey(
        'funding.PayoutAccount',
        null=True, blank=True,
        related_name='external_accounts',
        on_delete=models.CASCADE
    )

    status = models.CharField(max_length=40)

    @property
    def parent(self):
        return self.connect_account

    @property
    def ready(self):
        return True

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
        try:
            currencies = [f.target.currency for f in self.funding_set.all() if f.target]
            provider = self.provider_class.objects.filter(paymentcurrency__code__in=currencies).first()
            return provider.payment_methods
        except (AttributeError, self.provider_class.DoesNotExist) as e:
            logging.error(e)
            return []

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/external-accounts'

    public_data = {}

    def __str__(self):
        return "Bank account #{}".format(self.id)

    class Meta:
        ordering = ('id',)


class FundingPlatformSettings(BasePlatformSettings):

    anonymous_donations = models.BooleanField(
        _('Hide names from all donations'), default=False
    )
    allow_anonymous_rewards = models.BooleanField(
        _('Allow guests to donate rewards'), default=True
    )

    public_accounts = models.BooleanField(
        _('Allow users to select account from list of public accounts'),
        default=False,
        help_text=_('Allow users to select account from list of public accounts')
    )

    matching_name = models.CharField(
        _('Name to use for match funding'),
        max_length=60,
        null=True,
        blank=True,
        help_text=_('Change this if you want to use something else then the platform name for matching amounts.')
    )

    @property
    def stripe_publishable_key(self):
        from bluebottle.funding_stripe.utils import get_stripe_settings
        settings = get_stripe_settings()
        if settings:
            return settings['publishable_key']

    class Meta(object):
        verbose_name_plural = _('funding settings')
        verbose_name = _('funding settings')


from bluebottle.funding.periodic_tasks import *  # noqa
