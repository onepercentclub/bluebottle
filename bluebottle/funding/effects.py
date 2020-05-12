from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.funding.models import Payout


class GeneratePayouts(Effect):
    post_save = True
    conditions = []

    def execute(self):
        Payout.generate(self.instance)

    def __unicode__(self):
        return _('Generate payouts')
