from django.utils.translation import gettext_lazy as _
from bluebottle.fsm.effects import Effect

from bluebottle.funding.models import Funding


class PutActivitiesOnHoldEffect(Effect):
    conditions = []
    title = _("Put activities on hold")
    template = "admin/put_activities_on_hold.html"

    def post_save(self, **kwargs):
        fundings = Funding.objects.filter(
            status="open", bank_account__connect_account=self.instance
        )

        for funding in fundings:
            funding.states.put_on_hold(save=True)

    def __str__(self):
        return "Put activities on hold when payments are disabled by stripe"
