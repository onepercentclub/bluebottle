from django.utils.translation import pgettext

from bluebottle.activities.messages import ReviewerActivityNotification


class FundingSubmittedReviewerMessage(ReviewerActivityNotification):
    subject = pgettext(
        "email",
        "A new crowdfunding campaign is ready to be reviewed on {site_name}"
    )
    template = 'messages/reviewer/campaign_submitted'

    action_title = pgettext("email", "View campaign")
