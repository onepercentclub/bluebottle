import datetime

from django.db import models
from django.db.models.aggregates import Sum
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import DjangoChoices, ChoiceItem
from moneyed.classes import Money
from multiselectfield import MultiSelectField
from polymorphic.models import PolymorphicModel

from bluebottle.activities.models import Activity, Contribution
from bluebottle.files.fields import ImageField
from bluebottle.fsm import FSMField
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import MoneyField, get_currency_choices


class Funding(Activity):

    class Status(DjangoChoices):
        draft = ChoiceItem('draft', _('draft'))
        submitted = ChoiceItem('submitted', _('submitted'))
        approved = ChoiceItem('approved', _('approved'))
        open = ChoiceItem('open', _('open'))
        done = ChoiceItem('done', _('done'))
        closed = ChoiceItem('closed', _('closed'))

    deadline = models.DateField(_('deadline'), null=True, blank=True)
    duration = models.PositiveIntegerField(_('duration'), null=True, blank=True)

    target = MoneyField(null=True, blank=True)
    accepted_currencies = MultiSelectField(
        max_length=100, default=[],
        choices=lazy(get_currency_choices, tuple)()
    )

    account = models.ForeignKey('payouts.PayoutAccount', null=True)

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

    def deadline_in_future(self):
        return not self.deadline or self.deadline > timezone.now()

    def is_complete(self):
        from bluebottle.funding.serializers import FundingSubmitSerializer
        serializer = FundingSubmitSerializer(
            data=model_to_dict(self)
        )
        if not serializer.is_valid():
            print serializer.errors
            return _('Please make sure all required fields are filled in')

    def initiative_is_approved(self):
        if not self.initiative.status == 'approved':
            return _('Please make sure the initiative is approved')

    @Activity.status.transition(
        source=Status.draft,
        target=Status.submitted,
        conditions=[is_complete, initiative_is_approved]
    )
    def submit(self):
        pass

    @Activity.status.transition(
        source=Status.submitted,
        target=Status.approved,
        conditions=[is_complete, initiative_is_approved]
    )
    def approve(self):
        pass

    @Activity.status.transition(
        source=Status.approved,
        target=Status.open,
        conditions=[is_complete, initiative_is_approved]
    )
    def start(self):
        if self.duration:
            self.deadline = timezone.now().date() + datetime.timedelta(days=self.duration)

    @Activity.status.transition(
        source=Status.open,
        target=Status.done,
    )
    def done(self):
        pass

    @Activity.status.transition(
        source=Status.open,
        target=Status.closed,
    )
    def closed(self):
        pass

    @Activity.status.transition(
        source=[Status.done, Status.closed],
        target=Status.open,
        conditions=[deadline_in_future]
    )
    def extend(self):
        pass


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
            status=Donation.Status.success
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
            status=[Donation.Status.success]
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
    class Status(Contribution.Status):
        refunded = ChoiceItem('refunded', _('refunded'))

    amount = MoneyField()
    reward = models.ForeignKey(Reward, null=True, related_name="donations")
    fundraiser = models.ForeignKey(Fundraiser, null=True, related_name="donations")

    @property
    def payment_method(self):
        if not self.payment:
            return None
        return self.payment.type

    def funding_is_running(self):
        return self.activity.status == Funding.Status.open

    @Contribution.status.transition(
        source=[Status.new, Status.success],
        target=Status.refunded,
    )
    def refund(self):
        pass

    @Contribution.status.transition(
        source=[Status.new, Status.success],
        target=Status.failed,
    )
    def fail(self):
        pass

    @Contribution.status.transition(
        source=[Status.new, Status.failed],
        target=Status.success,
    )
    def success(self):
        pass


class Payment(PolymorphicModel):
    class Status(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        pending = ChoiceItem('pending', _('pending'))
        success = ChoiceItem('success', _('success'))
        refunded = ChoiceItem('refunded', _('refunded'))
        failed = ChoiceItem('failed', _('failed'))

    status = FSMField(
        default=Status.new,
        protected=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    donation = models.OneToOneField(Donation, related_name='payment')

    def can_refund(self):
        return self.status in ['pending', 'success']

    @Activity.status.transition(
        source=['new'],
        target='success'
    )
    def succeed(self):
        self.donation.success()
        self.donation.save()

    @Activity.status.transition(
        source=['new', 'success'],
        target='failed'
    )
    def fail(self):
        self.donation.fail()
        self.donation.save()

    @Activity.status.transition(
        source=['success'],
        target='refunded',
        # conditions=[can_refund]
    )
    def refund(self):
        raise NotImplementedError('Refunding not yet implemented for "{}"'.format(self))
        self.donation.refund()
        self.donation.save()

    def __unicode__(self):
        return "{} - {}".format(self.polymorphic_ctype, self.id)

    class Meta:
        permissions = (
            ('refund_payment', 'Can refund payments'),
        )
