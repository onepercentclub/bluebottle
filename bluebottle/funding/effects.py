from bluebottle.funding.models import MoneyContribution

from bluebottle.fsm.state import TransitionNotPossible
from future.utils import python_2_unicode_compatible

import datetime

from django.utils import timezone
from django.utils.timezone import get_current_timezone, now
from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.payouts_dorado.adapters import DoradoPayoutAdapter
from bluebottle.updates.models import Update
from bluebottle.wallposts.models import SystemWallpost


@python_2_unicode_compatible
class GeneratePayoutsEffect(Effect):
    conditions = []
    title = _('Generate payouts')
    template = 'admin/generate_payout_effect.html'

    def post_save(self, **kwargs):
        from bluebottle.funding.models import Payout
        try:
            Payout.generate(self.instance)
        except AssertionError:
            pass

    def __str__(self):
        return _('Generate payouts, so that payouts can be approved')


@python_2_unicode_compatible
class DeletePayoutsEffect(Effect):
    conditions = []
    title = _('Delete payouts')
    template = 'admin/delete_payout_effect.html'

    def post_save(self, **kwargs):
        self.instance.payouts.all().delete()

    def __str__(self):
        return _('Delete all related payouts')


@python_2_unicode_compatible
class UpdateFundingAmountsEffect(Effect):
    conditions = []
    title = _('Update amounts')

    display = False

    def post_save(self, **kwargs):
        self.instance.activity.update_amounts()

    def __str__(self):
        return _('Update total amounts')


@python_2_unicode_compatible
class UpdateDonationValueEffect(Effect):
    conditions = []
    title = _('Update contribution value')

    display = False

    def post_save(self, **kwargs):
        contribution = self.instance.contributions.first()
        if contribution:
            contribution.value = self.instance.payout_amount
            contribution.save()

    def __str__(self):
        return _('Update contribution value')


@python_2_unicode_compatible
class RemoveDonorFromPayoutEffect(Effect):
    conditions = []
    title = _('Remove donation from payout')

    display = False

    def pre_save(self, **kwargs):
        self.instance.payout = None

    def __str__(self):
        return _('Remove donation from payout')


@python_2_unicode_compatible
class SetDeadlineEffect(Effect):
    conditions = []
    title = _('Set deadline')
    template = 'admin/set_deadline_effect.html'

    def pre_save(self, **kwargs):
        if not self.instance.deadline:
            deadline = timezone.now() + datetime.timedelta(days=self.instance.duration)
            self.instance.deadline = get_current_timezone().localize(
                datetime.datetime(
                    deadline.year,
                    deadline.month,
                    deadline.day,
                    hour=23,
                    minute=59,
                    second=59
                )
            )

    def __str__(self):
        return _('Set deadline according to the duration')


@python_2_unicode_compatible
class RefundPaymentAtPSPEffect(Effect):

    title = _('Refund payment')

    template = 'admin/execute_refund_effect.html'

    def post_save(self, **kwargs):
        self.instance.refund()

    def __str__(self):
        return _('Request refund payment at PSP')


@python_2_unicode_compatible
class GenerateDonorWallpostEffect(Effect):
    conditions = []
    title = _('Create wall update')
    template = 'admin/generate_donation_wallpost_effect.html'

    def post_save(self, **kwargs):
        Update.objects.get_or_create(
            author=self.instance.user,
            contribution=self.instance,
            activity=self.instance.activity,
        )

    def __str__(self):
        return _('Generate wall update for donation')


@python_2_unicode_compatible
class RemoveDonorWallpostEffect(Effect):
    conditions = []
    title = _('Delete wallpost')
    template = 'admin/remove_donation_wallpost_effect.html'

    def post_save(self, **kwargs):
        SystemWallpost.objects.filter(
            author=self.instance.user,
            donation=self.instance,
        ).all().delete()

    def __str__(self):
        return _('Delete wallpost for donation')


@python_2_unicode_compatible
class SubmitConnectedActivitiesEffect(Effect):
    conditions = []
    title = _('Submit activities')
    template = 'admin/submit_connected_activities_effect.html'

    def post_save(self, **kwargs):
        for funding in self.instance.funding_set.filter(
                status__in=('draft', 'needs_work')
        ):
            try:
                funding.states.submit(save=True)
            except TransitionNotPossible:
                pass

    def __str__(self):
        return _('Submit connected activities')


@python_2_unicode_compatible
class DeleteDocumentEffect(Effect):
    conditions = []
    title = _('Delete uploaded document')
    template = 'admin/delete_uploaded_document_effect.html'

    def post_save(self, **kwargs):
        if self.instance.document:
            self.instance.document.delete()
            self.instance.document = None

    def __str__(self):
        return _('Delete verification documents, since they are no longer needed')


@python_2_unicode_compatible
class SubmitPayoutEffect(Effect):
    conditions = []

    title = _('Trigger payout')
    template = 'admin/submit_payout_effect.html'

    def post_save(self, **kwargs):
        adapter = DoradoPayoutAdapter(self.instance)
        adapter.trigger_payout()

    def __str__(self):
        return _('Trigger payout at the PSP')


@python_2_unicode_compatible
class BaseSetDateEffect(Effect):
    conditions = []
    field = 'date'
    title = _('Set date')

    display = False

    def pre_save(self, **kwargs):
        setattr(self.instance, self.field, timezone.now())

    def __str__(self):
        field = self.instance._meta.get_field(self.field)
        return _('Set {} to current date').format(field.verbose_name)


def SetDateEffect(_field):
    class _SetDateEffect(BaseSetDateEffect):
        field = _field

    return _SetDateEffect


@python_2_unicode_compatible
class ClearPayoutDatesEffect(Effect):
    conditions = []
    field = 'date'
    display = False

    def pre_save(self, **kwargs):
        self.instance.date_approved = None
        self.instance.date_started = None
        self.instance.date_completed = None

    def __str__(self):
        return _('Clear payout event dates')


@python_2_unicode_compatible
class CreateDonationEffect(Effect):
    conditions = []
    display = False

    def post_save(self, **kwargs):
        money_contribution = MoneyContribution(
            contributor=self.instance,
            start=now(),
            value=self.instance.amount
        )
        money_contribution.save()

    def __str__(self):
        return _('Create a donation')
