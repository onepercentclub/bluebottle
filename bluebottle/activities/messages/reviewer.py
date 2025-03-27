from django.db.models import Q
from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class ReviewerActivityNotification(TransitionMessage):
    context = {
        "title": "title",
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

        if self.obj.location and self.obj.location.subregion:
            recipients = recipients.filter(
                Q(subregion_manager=self.obj.location.subregion)
                | Q(subregion_manager__isnull=True)
            )

        return list(recipients)


class ActivitySubmittedNotification(ReviewerActivityNotification):

    subject = pgettext("email", "Activity submitted for review")
    template = "messages/reviewer/activity_submitted"
