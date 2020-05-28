import datetime

from django.utils import timezone
from django.utils.timezone import get_current_timezone
from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.funding.models import Payout
from bluebottle.payouts_dorado.adapters import DoradoPayoutAdapter
from bluebottle.wallposts.models import SystemWallpost


class GeneratePayoutsEffect(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        Payout.generate(self.instance)

    def __unicode__(self):
        return _('Generate payouts')


class DeletePayoutsEffect(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        self.instance.payouts.all().delete()

    def __unicode__(self):
        return _('Delete related payouts')


class UpdateFundingAmountsEffect(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        self.instance.activity.update_amounts()

    def __unicode__(self):
        return _('Update funding amounts')


class SetDeadlineEffect(Effect):
    post_save = False
    conditions = []

    def execute(self, **kwargs):
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

    def __unicode__(self):
        return _('Set deadline (if duration is set)')


class ExecuteRefundEffect(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        self.instance.refund()

    def __unicode__(self):
        return _('Refund payment at PSP')


class GenerateDonationWallpostEffect(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        SystemWallpost.objects.get_or_create(
            author=self.instance.user,
            donation=self.instance,
            defaults={
                'content_object': self.instance.activity,
                'related_object': self.instance
            }
        )

    def __unicode__(self):
        return _('Generate donation wallpost')


class RemoveDonationWallpostEffect(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        SystemWallpost.objects.filter(
            author=self.instance.user,
            donation=self.instance,
        ).all().delete()

    def __unicode__(self):
        return _('Delete donation wallpost')


class SubmitConnectedActivitiesEffect(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        for external_account in self.instance.external_accounts.all():
            for funding in external_account.funding_set.filter(
                    review_status__in=('draft', 'needs_work')
            ):
                funding.states.submit(save=True)

    def __unicode__(self):
        return _('Submit connected activities')


class DeleteDocumentEffect(Effect):
    post_save = False
    conditions = []

    def execute(self, **kwargs):
        if self.instance.document:
            self.instance.document.delete()
            self.instance.document = None

    def __unicode__(self):
        return _('Delete uploaded document')


class SubmitPayoutEffect(Effect):
    post_save = False
    conditions = []

    def execute(self, **kwargs):
        adapter = DoradoPayoutAdapter(self.instance)
        adapter.trigger_payout()

    def __unicode__(self):
        return _('Trigger payout')


class BaseSetDateEffect(Effect):
    post_save = False
    conditions = []
    field = 'date'

    def execute(self, **kwargs):
        setattr(self.instance, self.field, timezone.now())

    def __unicode__(self):
        field = self.instance._meta.get_field(self.field)
        return _('Set {} to current date').format(field.verbose_name)


def SetDateEffect(_field):

    class _SetDateEffect(BaseSetDateEffect):
        field = _field

    return _SetDateEffect


class ClearPayoutDatesEffect(Effect):
    post_save = False
    conditions = []
    field = 'date'

    def execute(self, **kwargs):
        self.instance.date_approved = None
        self.instance.date_started = None
        self.instance.date_completed = None

    def __unicode__(self):
        return _('Set date')
