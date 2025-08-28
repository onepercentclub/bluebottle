from django.utils.translation import pgettext

from bluebottle.activities.messages.reviewer import ReviewerActivityNotification


class GrantApplicationSubmittedReviewerMessage(ReviewerActivityNotification):
    subject = pgettext(
        "email",
        "A new grant application is ready to be reviewed on {site_name}"
    )
    template = 'messages/grant_application/reviewer/application_submitted'

    action_title = pgettext("email", "View application")
