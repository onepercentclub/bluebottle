from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.funding.models import Payout
from bluebottle.wallposts.models import SystemWallpost


class GeneratePayouts(Effect):
    post_save = True
    conditions = []

    def execute(self):
        Payout.generate(self.instance)

    def __unicode__(self):
        return _('Generate payouts')


class UpdateFundingAmounts(Effect):
    post_save = True
    conditions = []

    def execute(self):
        self.instance.activity.update_amounts()

    def __unicode__(self):
        return _('Update funding amounts')


class RefundPaymentAtPSP(Effect):
    post_save = True
    conditions = []

    def execute(self):
        self.instance.refund()

    def __unicode__(self):
        return _('Refund payment at PSP')


class GenerateDonationWallpost(Effect):
    post_save = True
    conditions = []

    def execute(self):
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


class RemoveDonationWallpost(Effect):
    post_save = True
    conditions = []

    def execute(self):
        SystemWallpost.objects.filter(
            author=self.instance.user,
            donation=self.instance,
        ).all().delete()

    def __unicode__(self):
        return _('Delete donation wallpost')
