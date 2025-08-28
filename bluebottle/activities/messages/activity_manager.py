from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.notifications.messages import TransitionMessage
from django.utils.html import format_html


class OwnerActivityNotification(TransitionMessage):
    context = {
        'title': 'title',
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    action_title = pgettext('email', 'Open your activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]


class ImpactReminderMessage(OwnerActivityNotification):
    subject = pgettext('email', 'Please share the impact results for your activity "{title}".')
    template = 'messages/activity_manager/activity_impact_reminder'
    context = {
        'title': 'title'
    }


class ActivitySucceededNotification(OwnerActivityNotification):
    """
    The activity succeeded
    """
    subject = pgettext('email', 'Your activity "{title}" has succeeded 🎉')
    template = 'messages/activity_manager/activity_succeeded'


class ActivityRestoredNotification(OwnerActivityNotification):
    """
    The activity was restored
    """
    subject = pgettext('email', 'The activity "{title}" has been restored')
    template = 'messages/activity_manager/activity_restored'


class ActivityRejectedNotification(OwnerActivityNotification):
    """
    The activity was rejected
    """
    subject = pgettext('email', 'Your activity "{title}" has been rejected')
    template = 'messages/activity_manager/activity_rejected'


class ActivityCancelledNotification(OwnerActivityNotification):
    """
    The activity got cancelled
    """
    subject = pgettext('email', 'Your activity "{title}" has been cancelled')
    template = 'messages/activity_manager/activity_cancelled'


class ActivityExpiredNotification(OwnerActivityNotification):
    """
    The activity expired (no sign-ups before registration deadline or start date)
    """
    subject = pgettext('email', 'The registration deadline for your activity "{title}" has expired')
    template = 'messages/activity_manager/activity_expired'


class ActivityPublishedNotification(OwnerActivityNotification):
    """
    The activity was published
    """
    subject = pgettext('email', "Your activity on {site_name} has been published!")
    template = 'messages/activity_manager/activity_published'


class ActivitySubmittedNotification(OwnerActivityNotification):
    """
    The activity was submitted
    """
    subject = pgettext('email', "You submitted an activity on {site_name}")
    template = 'messages/activity_manager/activity_submitted'


class ActivityApprovedNotification(OwnerActivityNotification):
    """
    The activity was approved
    """
    subject = pgettext('email', "Your activity on {site_name} has been approved!")
    template = 'messages/activity_manager/activity_approved'


class ActivityNeedsWorkNotification(OwnerActivityNotification):
    """
    The activity needs work
    """
    subject = pgettext('email', "The activity you submitted on {site_name} needs work")
    template = 'messages/activity_manager/activity_needs_work'


class PublishActivityReminderNotification(OwnerActivityNotification):
    subject = pgettext('email', 'Publish your activity "{title}"')
    template = 'messages/activity_manager/publish_activity_reminder'
    send_once = True

    context = {
        'title': 'title',
    }

    action_title = pgettext('email', 'Publish your activity')


class TermsOfServiceNotification(OwnerActivityNotification):
    subject = pgettext('email', 'Terms of service')
    template = 'messages/activity_manager/terms_of_service'
    send_once = False

    def get_bcc_addresses(self):
        settings = InitiativePlatformSettings.load()
        if settings.bcc_terms_of_service:
            return [settings.bcc_terms_of_service]

        return []

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context['partner_organization'] = (
            self.obj.organization and self.obj.organization.name or self.obj.owner.full_name
        )
        settings = InitiativePlatformSettings.load()
        template = settings.terms_of_service_mail_text or settings.terms_of_service
        template = template.replace('\n', '<br />')
        context['terms_of_service'] = format_html(template, **context)
        return context
