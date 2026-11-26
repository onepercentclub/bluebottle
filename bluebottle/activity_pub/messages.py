from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.activities.messages.activity_manager import OwnerActivityNotification


class AdoptionCancelledNotification(OwnerActivityNotification):
    """
    Notify the activity manager that a partner platform cancelled its copy of the activity.
    The activity itself stays open, so this is sent outside of an activity transition.
    """
    subject = pgettext(
        'platform-email', 'Your activity "{title}" has been cancelled on {partner_name}'
    )
    template = 'messages/activity_manager/adoption_cancelled'
