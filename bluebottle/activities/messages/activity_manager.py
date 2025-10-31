from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.funding.models import Funding
from bluebottle.grant_management.models import GrantApplication
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.notifications.messages import TransitionMessage
from django.utils.html import format_html


class OwnerActivityNotification(TransitionMessage):
    """
    Base class for all notifications to activity managers.
    """

    context = {
        'title': 'title',
    }

    @property
    def action_link(self):
        return self.obj.get_absolute_url()

    def get_context(self, recipient):
        context = super().get_context(recipient)
        if isinstance(self.obj, Funding):
            context['activity_type'] = pgettext('email', 'crowdfunding campaign')
        elif isinstance(self.obj, GrantApplication):
            context['activity_type'] = pgettext('email', 'grant application')
        else:
            context['activity_type'] = pgettext('email', 'activity')

        return context

    @property
    def action_title(self):
        if isinstance(self.obj, Funding):
            return pgettext('email', 'View campaign')
        elif isinstance(self.obj, GrantApplication):
            return pgettext('email', 'View application')
        else:
            return pgettext('email', 'View activity')

    def get_recipients(self):
        """activity owner"""
        return [self.obj.owner]

    class Meta:
        abstract = True


class ImpactReminderMessage(OwnerActivityNotification):
    """
    Remind the activity manager to add impact results to their activity.
    """
    subject = pgettext('email', 'Please share the impact results for your activity "{title}".')
    template = 'messages/activity_manager/activity_impact_reminder'
    context = {
        'title': 'title'
    }


class ActivitySucceededNotification(OwnerActivityNotification):
    """
    Notify the activity manager that the activity succeeded.
    """
    subject = pgettext('email', 'Your activity "{title}" has succeeded 🎉')
    template = 'messages/activity_manager/activity_succeeded'


class ActivityRestoredNotification(OwnerActivityNotification):
    """
    Notify the activity manager that the activity was restored
    """
    subject = pgettext('email', 'The activity "{title}" has been restored')
    template = 'messages/activity_manager/activity_restored'


class ActivityRejectedNotification(OwnerActivityNotification):
    """
    Notify the activity manager that the activity was rejected
    """
    subject = pgettext('email', 'Your activity "{title}" has been rejected')
    template = 'messages/activity_manager/activity_rejected'


class ActivityCancelledNotification(OwnerActivityNotification):
    """
    Notify the activity manager that the activity got cancelled
    """
    subject = pgettext('email', 'Your activity "{title}" has been cancelled')
    template = 'messages/activity_manager/activity_cancelled'


class ActivityExpiredNotification(OwnerActivityNotification):
    """
    Notify the activity manager that the activity expired (no sign-ups before registration deadline or start date)
    """
    subject = pgettext('email', 'The registration deadline for your activity "{title}" has expired')
    template = 'messages/activity_manager/activity_expired'


class ActivityPublishedNotification(OwnerActivityNotification):
    """
    Notify the activity manager that the activity was published
    """
    subject = pgettext('email', "Your activity on {site_name} has been published!")
    template = 'messages/activity_manager/activity_published'


class ActivitySubmittedNotification(OwnerActivityNotification):
    """
    Notify the activity manager that the activity was submitted
    """
    subject = pgettext('email', "You submitted an activity on {site_name}")
    template = 'messages/activity_manager/activity_submitted'


class ActivityApprovedNotification(OwnerActivityNotification):
    """
    Notify the activity manager that the activity was approved
    """
    subject = pgettext('email', "Your activity on {site_name} has been approved!")
    template = 'messages/activity_manager/activity_approved'


class ActivityNeedsWorkNotification(OwnerActivityNotification):
    """
    Notify the activity manager that the activity needs work
    """
    subject = pgettext('email', "The activity you submitted on {site_name} needs work")
    template = 'messages/activity_manager/activity_needs_work'


class PublishActivityReminderNotification(OwnerActivityNotification):
    """
    Notify the activity manager that an activity still needs to be published
    """
    subject = pgettext('email', 'Publish your activity "{title}"')
    template = 'messages/activity_manager/publish_activity_reminder'
    send_once = True

    context = {
        'title': 'title',
    }

    action_title = pgettext('email', 'Publish your activity')


class TermsOfServiceNotification(OwnerActivityNotification):
    """
    Notify the activity manager about the terms of service they accepted.
    A BCC will be sent to other email address if configured.
    """
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
