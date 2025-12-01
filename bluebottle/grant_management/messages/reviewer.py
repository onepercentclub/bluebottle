from django.utils.translation import pgettext

from bluebottle.activities.messages.reviewer import ReviewerActivityNotification


class GrantApplicationSubmittedReviewerMessage(ReviewerActivityNotification):
    subject = pgettext(
        "email",
        "A new grant application is ready to be reviewed on {site_name}"
    )
    template = 'messages/grant_application/reviewer/application_submitted'

    action_title = pgettext("email", "View application")


class PayoutReadyForApprovalMessage(ReviewerActivityNotification):
    """
    Notify reviewers when a payout is ready for approval
    """
    subject = pgettext(
        "email",
        "You have grant payout to approve on {site_name}"
    )
    template = 'messages/grant_application/reviewer/payout_ready_for_approval'

    action_title = pgettext("email", "Complete payout")

    def get_context(self, recipient):
        context = super().get_context(recipient)
        grant = self.obj.grant
        context['grant'] = grant
        context['requester'] = self.obj.activity.owner.full_name
        context['grant_fund'] = grant.fund.name
        context['title'] = self.obj.activity.title
        context['amount'] = self.obj.amount
        return context

    @property
    def action_link(self):
        return self.obj.get_admin_url()
