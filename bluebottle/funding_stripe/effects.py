from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from django_tools.middlewares.ThreadLocal import get_current_request

from bluebottle.fsm.effects import Effect
from bluebottle.funding.models import Funding
from bluebottle.utils.utils import get_client_ip

from bluebottle.funding_stripe.utils import get_stripe


class AcceptTosEffect(Effect):
    def post_save(self, **kwargs):
        if self.instance.tos_accepted:
            stripe = get_stripe()

            stripe.Account.modify(
                self.instance.account_id,
                tos_acceptance={
                    "service_agreement": "full",
                    "date": now(),
                    "ip": get_client_ip(get_current_request()),
                },
            )


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
