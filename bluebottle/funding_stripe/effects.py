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

            service_argreement = (
                self.instance.account.tos_acceptance.service_agreement if
                hasattr(self.instance.account.tos_acceptance, 'service_agreement') else 
                "full"
            )

            stripe.Account.modify(
                self.instance.account_id,
                tos_acceptance={
                    "service_agreement": service_argreement,
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


class OpenActivitiesOnHoldEffect(Effect):
    conditions = []
    title = _("Open activities that are on hold")
    template = "admin/open_activities_on_hold.html"

    def post_save(self, **kwargs):
        fundings = Funding.objects.filter(
            status="on_hold", bank_account__connect_account=self.instance
        )

        for funding in fundings:
            funding.states.approve(save=True)

    def __str__(self):
        return "Open activities that are on hold when payments are verified again by stripe"


class UpdateBusinessTypeEffect(Effect):
    conditions = []
    title = _("Update business type at stripe")
    display = False

    def pre_save(self, **kwargs):
        stripe = get_stripe()
        account = self.instance

        if account.account_id:

            stripe_account = stripe.Account.modify(
                account.account_id,
                business_type=account.business_type
            )
            account.update(stripe_account, save=False)

    def __str__(self):
        return "Update bussiness type at stripe. This might result in addiontional verfication requirements"
