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
    title = _('Generate payouts')
    template = 'admin/generate_payout_effect.html'

    def execute(self, **kwargs):
        Payout.generate(self.instance)

    def __unicode__(self):
        return _('Generate payouts, so that payouts can be approved')


class DeletePayoutsEffect(Effect):
    post_save = True
    conditions = []
    title = _('Delete payouts')
    template = 'admin/delete_payout_effect.html'

    def execute(self, **kwargs):
        self.instance.payouts.all().delete()

    def __unicode__(self):
        return _('Delete all related payouts')


class UpdateFundingAmountsEffect(Effect):
    post_save = True
    conditions = []
    title = _('Update amounts')

    display = False

    def execute(self, **kwargs):
        self.instance.activity.update_amounts()

    def __unicode__(self):
        return _('Update total amounts')


class SetDeadlineEffect(Effect):
    post_save = False
    conditions = []
    title = _('Set deadline')
    template = 'admin/set_deadline_effect.html'

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
        return _('Set deadline according to the duration')


class RefundPaymentAtPSPEffect(Effect):
    post_save = False

    title = _('Refund payment')

    template = 'admin/execute_refund_effect.html'

    def execute(self, **kwargs):
        self.instance.refund()

    def __unicode__(self):
        return _('Request refund payment at PSP')


class GenerateDonationWallpostEffect(Effect):
    post_save = True
    conditions = []
    title = _('Create wallpost')
    template = 'admin/generate_donation_wallpost_effect.html'

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
        return _('Generate wallpost for donation')


class RemoveDonationWallpostEffect(Effect):
    post_save = True
    conditions = []
    title = _('Delete wallpost')
    template = 'admin/remove_donation_wallpost_effect.html'

    def execute(self, **kwargs):
        SystemWallpost.objects.filter(
            author=self.instance.user,
            donation=self.instance,
        ).all().delete()

    def __unicode__(self):
        return _('Delete wallpost for donation')


class SubmitConnectedActivitiesEffect(Effect):
    post_save = True
    conditions = []
    title = _('Submit activities')
    template = 'admin/submit_connected_activities_effect.html'

    def execute(self, **kwargs):
        for external_account in self.instance.external_accounts.all():
            for funding in external_account.funding_set.filter(
                    status__in=('draft', 'needs_work')
            ):
                funding.states.submit(save=True)

    def __unicode__(self):
        return _('Submit connected activities')


class DeleteDocumentEffect(Effect):
    post_save = False
    conditions = []
    title = _('Delete uploaded document')
    template = 'admin/delete_uploaded_document_effect.html'

    def execute(self, **kwargs):
        if self.instance.document:
            self.instance.document.delete()
            self.instance.document = None

    def __unicode__(self):
        return _('Delete verification documents, since they are no longer needed')


class SubmitPayoutEffect(Effect):
    post_save = True
    conditions = []
    title = _('Trigger payout')
    template = 'admin/submit_payout_effect.html'

    def execute(self, **kwargs):
        adapter = DoradoPayoutAdapter(self.instance)
        adapter.trigger_payout()

    def __unicode__(self):
        return _('Trigger payout at the PSP')


class BaseSetDateEffect(Effect):
    post_save = False
    conditions = []
    field = 'date'
    title = _('Set date')

    display = False

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
    display = False

    def execute(self, **kwargs):
        self.instance.date_approved = None
        self.instance.date_started = None
        self.instance.date_completed = None

    def __unicode__(self):
        return _('Clear payout event dates')
