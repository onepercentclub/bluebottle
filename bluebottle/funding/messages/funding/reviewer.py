from django.utils.translation import pgettext

from bluebottle.activities.messages.reviewer import ReviewerActivityNotification


class FundingSubmittedReviewerMessage(ReviewerActivityNotification):
    """
    Notify platform managers that a new crowdfunding campaign has been submitted as is ready to be reviewed.
    """
    subject = pgettext(
        "platform-email",
        "A new crowdfunding campaign is ready to be reviewed on {site_name}"
    )
    template = 'messages/funding/reviewer/campaign_submitted'

    action_title = pgettext("platform-email", "View campaign")
