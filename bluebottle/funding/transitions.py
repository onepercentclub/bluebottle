import datetime

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.activities.transitions import ActivityTransitions, ContributionTransitions
from bluebottle.fsm import transition, ModelTransitions
from bluebottle.funding.messages import (
    DonationSuccessActivityManagerMessage, DonationSuccessDonorMessage,
    DonationRefundedDonorMessage, FundingRealisedOwnerMessage,
    FundingClosedMessage, FundingPartiallyFundedMessage
)
from bluebottle.payouts_dorado.adapters import DoradoPayoutAdapter


class FundingTransitions(ActivityTransitions):
    serializer = 'bluebottle.funding.serializers.FundingSubmitSerializer'

    class values(ActivityTransitions.values):
        partially_funded = ChoiceItem('partially_funded', _('partially funded'))
        refunded = ChoiceItem('refunded', _('refunded'))

    def deadline_in_future(self):
        if not self.instance.deadline or self.instance.deadline < timezone.now():
            return _("Please select a new deadline in the future before extending.")

    @transition(
        source=values.in_review,
        target=values.open,
        permissions=[ActivityTransitions.can_approve]
    )
    def reviewed(self):
        if self.instance.duration and not self.instance.deadline:
            self.instance.deadline = timezone.now() + datetime.timedelta(days=self.instance.duration)

    @transition(
        source=values.open,
        target=values.partially_funded,
        messages=[FundingPartiallyFundedMessage]
    )
    def partial(self):
        pass

    @transition(
        source=[values.open, values.succeeded],
        target=values.succeeded,
        messages=[FundingRealisedOwnerMessage]
    )
    def succeed(self):
        from bluebottle.funding.models import Payout
        Payout.generate(self.instance)

    @transition(
        source=values.partially_funded,
        target=values.succeeded,
    )
    def approve(self):
        pass

    @transition(
        source=values.partially_funded,
        target=values.refunded,
    )
    def refund(self):
        pass

    @transition(
        source='*',
        target=values.closed,
        messages=[FundingClosedMessage]
    )
    def close(self):
        pass

    @transition(
        source=[
            values.partially_funded, values.closed, values.succeeded
        ],
        target=values.open,
        conditions=[deadline_in_future]
    )
    def extend(self):
        pass


class DonationTransitions(ContributionTransitions):
    class values(ContributionTransitions.values):
        refunded = ChoiceItem('refunded', _('refunded'))

    def funding_is_open(self):
        return self.instance.activity.status == FundingTransitions.values.open

    def update_funding(self):
        # Invalidate cached amount_donated on funding
        try:
            del self.instance.activity.amount_donated
        except AttributeError:
            pass

    @transition(
        source=[values.new, values.succeeded],
        target=values.refunded,
        messages=[
            DonationRefundedDonorMessage
        ]
    )
    def refund(self):
        self.update_funding()

    @transition(
        source=[values.new, values.succeeded],
        target=values.failed,
    )
    def fail(self):
        self.update_funding()

    @transition(
        source=[values.new, values.failed],
        target=values.succeeded,
        messages=[
            DonationSuccessActivityManagerMessage,
            DonationSuccessDonorMessage
        ]
    )
    def succeed(self):
        self.update_funding()


class PaymentTransitions(ModelTransitions):
    class values(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        pending = ChoiceItem('pending', _('pending'))
        succeeded = ChoiceItem('succeeded', _('succeeded'))
        refunded = ChoiceItem('refunded', _('refunded'))
        refund_requested = ChoiceItem('refund_requested', _('refund requested'))
        failed = ChoiceItem('failed', _('failed'))

    @transition(
        source=[values.new, values.failed],
        target=values.succeeded
    )
    def succeed(self):
        self.instance.donation.transitions.succeed()
        self.instance.donation.save()

    @transition(
        source=[values.new, values.succeeded],
        target=values.failed
    )
    def fail(self):
        self.instance.donation.transitions.fail()
        self.instance.donation.save()

    @transition(
        source=[values.succeeded],
        target=values.refunded
    )
    def refund(self):
        self.instance.donation.transitions.refund()
        self.instance.donation.save()


class PayoutTransitions(ModelTransitions):
    class values(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        approved = ChoiceItem('approved', _('approved'))
        started = ChoiceItem('started', _('started'))
        succeeded = ChoiceItem('succeeded', _('succeeded'))
        failed = ChoiceItem('failed', _('failed'))

    @transition(
        source=['*'],
        target=values.approved
    )
    def approve(self):
        adapter = DoradoPayoutAdapter(self.instance.activity)
        adapter.trigger_payout()

    @transition(
        source=['*'],
        target=values.new
    )
    def draft(self):
        pass

    @transition(
        source=['*'],
        target=values.started
    )
    def start(self):
        pass

    @transition(
        source=['*'],
        target=values.succeeded
    )
    def succeed(self):
        pass

    @transition(
        source=['*'],
        target=values.failed
    )
    def fail(self):
        pass


class PayoutAccountTransitions(ModelTransitions):
    class values(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        pending = ChoiceItem('pending', _('pending'))
        verified = ChoiceItem('verified', _('verified'))
        rejected = ChoiceItem('rejected', _('rejected'))


class PlainPayoutAccountTransitions(PayoutAccountTransitions):
    @transition(
        source=[PayoutAccountTransitions.values.new, PayoutAccountTransitions.values.rejected],
        target=PayoutAccountTransitions.values.pending
    )
    def submit(self):
        pass

    @transition(
        source=[
            PayoutAccountTransitions.values.pending,
            PayoutAccountTransitions.values.rejected,
            PayoutAccountTransitions.values.new
        ],
        target='verified'
    )
    def verify(self):
        self.instance.document.delete()
        self.instance.document = None
        self.instance.save()

    @transition(
        source=[PayoutAccountTransitions.values.pending, PayoutAccountTransitions.values.verified],
        target=PayoutAccountTransitions.values.rejected
    )
    def reject(self):
        self.instance.document.delete()
        self.instance.document = None
        self.instance.save()
