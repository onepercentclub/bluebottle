from django.utils.translation import pgettext
from djmoney.money import Money

from bluebottle.notifications.messages import TransitionMessage


class GrantPaymentRequestMessage(TransitionMessage):
    subject = pgettext(
        "email",
        "A grant payment request is ready on {site_name}"
    )
    template = 'messages/grant_application/grant_provider/grant_payment_request'
    context = {
        "title": "title",
    }

    def payout_details(self, payout):
        return {
            'id': payout.id,
            'amount': payout.total_amount,
            'fund': payout.grants.first().fund.name,
            'title': payout.activity.title,
        }

    def get_context(self, recipient):
        context = super(GrantPaymentRequestMessage, self).get_context(recipient)
        context['total'] = Money(self.obj.total.amount.amount, self.obj.total.amount.currency)
        context['payouts'] = [
            self.payout_details(payout)
            for payout in self.obj.payouts.all()
        ]
        return context

    action_title = pgettext("email", "Pay now")

    @property
    def action_link(self):
        return self.obj.get_admin_url()

    def get_recipients(self):
        return [self.obj.grant_provider.owner]
