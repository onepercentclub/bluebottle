from django.db.models import Q
from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class ReviewerActivityNotification(TransitionMessage):
    context = {
        "title": "title",
        "initiator_name": "owner.full_name",
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext("email", "View this activity")

    def get_recipients(self):
        """reviewers for this activity"""
        from bluebottle.members.models import Member

        recipients = Member.objects.filter(
            Q(is_staff=True) | Q(is_superuser=True)
        ).filter(submitted_initiative_notifications=True)

        if self.obj.office_location and self.obj.office_location.subregion:
            recipients = recipients.filter(
                Q(subregion_manager=self.obj.office_location.subregion)
                | Q(subregion_manager__isnull=True)
            )
        return list(recipients)


class ActivitySubmittedReviewerNotification(ReviewerActivityNotification):

    subject = pgettext("email", "A new activity is ready to be reviewed on {site_name}")
    template = "messages/reviewer/activity_submitted"


class ActivityPublishedReviewerNotification(ReviewerActivityNotification):

    subject = pgettext("email", "A new activity has been published on {site_name}")
    template = "messages/reviewer/activity_published"
