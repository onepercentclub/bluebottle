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
        return self.obj.get_admin_url()

    def get_action_link(self, recipient):
        if not recipient.is_staff and not recipient.is_superuser:
            return self.obj.get_absolute_url()
        return super().get_action_link(recipient)

    action_title = pgettext("platform-email", "View this activity")

    @property
    def activity(self):
        return self.obj

    def get_recipients(self):
        """reviewers for this activity"""
        from bluebottle.members.models import Member

        recipients = Member.objects.filter(
            submitted_initiative_notifications=True
        ).filter(
            Q(submitted_initiative_notifications=True)
            | Q(is_staff=True)
            | Q(is_superuser=True)
            | Q(
                user_permissions__codename='api_review_activity',
                user_permissions__content_type__app_label='activities'
            )
            | Q(
                groups__permissions__codename='api_review_activity',
                groups__permissions__content_type__app_label='activities'
            )
        ).distinct()

        if self.activity.office_location and self.activity.office_location.subregion:
            recipients = recipients.filter(
                Q(subregion_manager=self.activity.office_location.subregion)
                | Q(subregion_manager__isnull=True)
            )
        if self.activity.segments.exists():
            recipients = recipients.filter(
                Q(segment_manager__in=self.activity.segments.all())
                | Q(segment_manager__isnull=True)
            )
        return list(recipients)

    class Meta:
        abstract = True


class ActivitySubmittedReviewerNotification(ReviewerActivityNotification):

    subject = pgettext("platform-email", "A new activity is ready to be reviewed on {site_name}")
    template = "messages/reviewer/activity_submitted"


class ActivityPublishedReviewerNotification(ReviewerActivityNotification):

    subject = pgettext("platform-email", "A new activity has been published on {site_name}")
    template = "messages/reviewer/activity_published"

    @property
    def action_link(self):
        return self.obj.get_absolute_url()
