from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.activities.messages.reviewer import ReviewerActivityNotification


class ActivityRegisteredReviewerNotification(ReviewerActivityNotification):

    subject = pgettext("platform-email", "A new activity has been registered on {site_name}")
    template = "messages/reviewer/activity_registered"

    @property
    def action_link(self):
        return self.obj.get_absolute_url()
