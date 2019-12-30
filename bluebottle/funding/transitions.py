import datetime

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.activities.transitions import ActivityTransitions, ContributionTransitions
from bluebottle.fsm import transition, ModelTransitions, TransitionNotPossible
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

    def target_reached(self):
        if not self.instance.amount_raised >= self.instance.target:
            return _("Amount raised should at least equal to target amount.")

    def deadline_in_future(self):
        if not self.instance.deadline >= timezone.now():
            return _("The deadline of the activity should be in the future.")

    @transition(
        source=values.in_review,
        target=values.open,
        permissions=[ActivityTransitions.can_approve],
    )
    def reviewed(self):
        if self.instance.duration and not self.instance.deadline:
            deadline = timezone.now() + datetime.timedelta(days=self.instance.duration)
            self.instance.deadline = deadline.replace(hour=23, minute=59, second=59)

    @transition(
        source=values.open,
        target=values.partially_funded,
        messages=[FundingPartiallyFundedMessage],
        permissions=[ActivityTransitions.is_system]
    )
    def partial(self):
        from bluebottle.funding.models import Payout
        Payout.generate(self.instance)

    @transition(
        source=[values.open],
        target=values.succeeded,
        messages=[FundingRealisedOwnerMessage],
        permissions=[ActivityTransitions.is_system]
    )
    def succeed(self):
        from bluebottle.funding.models import Payout
        Payout.generate(self.instance)

    @transition(
        source=[values.succeeded, values.partially_funded],
        target=values.open,
        conditions=[deadline_in_future],
        permissions=[ActivityTransitions.can_approve]
    )
    def extend(self):
        pass

    @transition(
        source=[values.succeeded, values.partially_funded],
        target=values.succeeded,
        permissions=[ActivityTransitions.can_approve],
        conditions=[target_reached]
    )
    def recalculate(self):
        from bluebottle.funding.models import Payout
        Payout.generate(self.instance)

    @transition(
        source=values.partially_funded,
        target=values.succeeded,
        permissions=[ActivityTransitions.can_approve],
    )
    def approve(self):
        pass

    @transition(
        source=values.partially_funded,
        target=values.refunded,
    )
    def refund(self):
        for donation in self.instance.contributions.filter(status__in=['succeeded']).all():
            donation.payment.transitions.request_refund()
            donation.payment.save()
        for payout in self.instance.payouts.all():
            payout.transitions.cancel()
            payout.save()

    @transition(
        source=[
            values.in_review,
            values.refunded
        ],
        target=values.closed,
        messages=[FundingClosedMessage],
        permissions=[ActivityTransitions.can_approve],
    )
    def close(self):
        pass


class DonationTransitions(ContributionTransitions):
    class values(ContributionTransitions.values):
        refunded = ChoiceItem('refunded', _('refunded'))

    def funding_is_open(self):
        return self.instance.activity.status == FundingTransitions.values.open

    @transition(
        source=[values.new, values.succeeded],
        target=values.refunded,
        messages=[
            DonationRefundedDonorMessage
        ]
    )
    def refund(self):
        pass

    @transition(
        source=[values.new, values.succeeded],
        target=values.failed,
    )
    def fail(self):
        pass

    @transition(
        source=[values.new, values.failed],
        target=values.succeeded,
        messages=[
            DonationSuccessActivityManagerMessage,
            DonationSuccessDonorMessage
        ]
    )
    def succeed(self):
        parent = self.instance.fundraiser or self.instance.activity
        from bluebottle.wallposts.models import SystemWallpost
        pass
        SystemWallpost.objects.get_or_create(
            author=self.instance.user,
            donation=self.instance,
            defaults={
                'content_object': parent,
                'related_object': self.instance
            }
        )


class PaymentTransitions(ModelTransitions):
    class values(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        pending = ChoiceItem('pending', _('pending'))
        succeeded = ChoiceItem('succeeded', _('succeeded'))
        refunded = ChoiceItem('refunded', _('refunded'))
        refund_requested = ChoiceItem('refund_requested', _('refund requested'))
        failed = ChoiceItem('failed', _('failed'))

    @transition(
        source=[values.new, values.failed, values.refunded],
        target=values.succeeded
    )
    def succeed(self):
        try:
            self.instance.donation.transitions.succeed()
            self.instance.donation.save()
        except TransitionNotPossible:
            pass
        self.instance.donation.activity.update_amounts()

    @transition(
        source=[values.new, values.succeeded, values.refunded],
        target=values.failed
    )
    def fail(self):
        try:
            self.instance.donation.transitions.fail()
            self.instance.donation.save()
        except TransitionNotPossible:
            pass
        self.instance.donation.activity.update_amounts()

    @transition(
        source=[values.succeeded, values.refund_requested, values.failed],
        target=values.refunded
    )
    def refund(self):
        try:
            self.instance.donation.transitions.refund()
            self.instance.donation.save()
        except TransitionNotPossible:
            pass
        self.instance.donation.activity.update_amounts()


class PayoutTransitions(ModelTransitions):
    class values(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        approved = ChoiceItem('approved', _('approved'))
        started = ChoiceItem('started', _('started'))
        succeeded = ChoiceItem('succeeded', _('succeeded'))
        failed = ChoiceItem('failed', _('failed'))
        cancelled = ChoiceItem('cancelled', _('cancelled'))

    @transition(
        source=['*'],
        target=values.approved
    )
    def approve(self):
        self.instance.date_approved = timezone.now()
        adapter = DoradoPayoutAdapter(self.instance)
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
        self.instance.date_started = timezone.now()

    @transition(
        source=['*'],
        target=values.succeeded
    )
    def succeed(self):
        self.instance.date_completed = timezone.now()

    @transition(
        source=['*'],
        target=values.failed
    )
    def fail(self):
        pass

    @transition(
        source=['*'],
        target=values.cancelled
    )
    def cancel(self):
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
        if self.instance.document:
            self.instance.document.delete()
            self.instance.document = None

        for external_account in self.instance.external_accounts.all():
            for funding in external_account.funding_set.filter(
                review_status__in=('draft', 'needs_work')
            ):
                try:
                    funding.review_transitions.submit()
                except TransitionNotPossible:
                    pass

        self.instance.save()

    @transition(
        source=[PayoutAccountTransitions.values.pending, PayoutAccountTransitions.values.verified],
        target=PayoutAccountTransitions.values.rejected
    )
    def reject(self):
        if self.instance.document:
            self.instance.document.delete()
            self.instance.document = None
        self.instance.save()
