from django.db.models import Q
from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class InitiativeReviewerMessage(TransitionMessage):

    context = {
        'title': 'title',
        'initiator_name': 'owner.full_name',
    }

    @property
    def action_link(self):
        return self.obj.get_admin_url()

    action_title = pgettext('platform-email', 'View initiative')

    def get_recipients(self):
        """enabled staff members"""
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

    class Meta:
        abstract = True


class InitiativeSubmittedReviewerMessage(InitiativeReviewerMessage):
    subject = pgettext('platform-email', 'A new initiative is ready to be reviewed on {site_name}')
    template = 'messages/reviewer/initiative_submitted'


class InitiativePublishedReviewerMessage(InitiativeReviewerMessage):
    subject = pgettext('platform-email', 'A new initiative has been published on {site_name}!')
    template = 'messages/reviewer/initiative_published'

    @property
    def action_link(self):
        return self.obj.get_absolute_url()


class AssignedReviewerMessage(InitiativeReviewerMessage):
    subject = pgettext('platform-email', 'You are assigned to review "{title}".')
    template = 'messages/reviewer/assigned_reviewer'

    send_once = True

    def get_recipients(self):
        """the reviewer"""
        return [self.obj.reviewer]
