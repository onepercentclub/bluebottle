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

from bluebottle.fsm import FSMField, TransitionNotAllowed

from bluebottle.activities.models import Activity, Contribution
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import MoneyField, get_currency_choices


class Funding(Activity):

    class Status(DjangoChoices):
        draft = ChoiceItem('draft', _('draft'))
        submitted = ChoiceItem('submitted', _('submitted'))
        running = ChoiceItem('running', _('running'))
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

    def save(self, *args, **kwargs):
        if self.status == Activity.Status.draft:
            try:
                self.open()
            except TransitionNotAllowed:
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
        source=Activity.Status.open,
        target=Activity.Status.running,
        conditions=[is_complete, initiative_is_approved]
    )
    def start(self):
        if self.duration:
            self.deadline = timezone.now().date() + datetime.timedelta(days=self.duration)

    @Activity.status.transition(
        source=Activity.Status.running,
        target=Activity.Status.done,
    )
    def done(self):
        pass

    @Activity.status.transition(
        source=Activity.Status.running,
        target=Activity.Status.closed,
    )
    def closed(self):
        pass

    @Activity.status.transition(
        source=[Activity.Status.done, Activity.Status.closed],
        target=Activity.Status.running,
        conditions=[deadline_in_future]
    )
    def extend(self):
        pass


class Donation(Contribution):
    class Status(Contribution.Status):
        refunded = ChoiceItem('refunded', _('refunded'))

    amount = MoneyField()

    def funding_is_running(self):
        return self.activity.status == Activity.Status.open

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
