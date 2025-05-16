from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.activities.messages.activity_manager import OwnerActivityNotification


class ActivityRegisteredNotification(OwnerActivityNotification):
    """
    The activity was published
    """
    subject = pgettext('email', "Your activity on {site_name} has been registered!")
    template = 'messages/activity_manager/activity_registered'


class PastActivitySubmittedNotification(OwnerActivityNotification):
    """
    The activity was submitted
    """
    subject = pgettext('email', "You submitted an activity on {site_name}")
    template = 'messages/activity_manager/past_activity_submitted'


class PastActivityApprovedNotification(OwnerActivityNotification):
    """
    The activity was approved
    """
    subject = pgettext('email', "Your activity on {site_name} has been approved!")
    template = 'messages/activity_manager/past_activity_approved'
