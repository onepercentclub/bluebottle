from django.conf import settings
from django.utils.translation import gettext_lazy as _, pgettext_lazy as pgettext

from bluebottle.members.models import Member
from bluebottle.notifications.messages import TransitionMessage


class LivePayoutAccountMarkedIncomplete(TransitionMessage):
    """
    A payout account that is connected to a live crowdfunding campaign was marked incomplete
    """
    subject = pgettext('email', u'Live campaign identity verification failed!')
    template = 'messages/platform_manager/live_payout_account_rejected'

    context = {
        'id': 'id'
    }

    def get_recipients(self):
        """platform support email addresses"""
        members = []
        for email in settings.SUPPORT_EMAIL_ADDRESSES:
            member, _c = Member.objects.get_or_create(email=email)
            members.append(member)
        for member in Member.objects.filter(submitted_initiative_notifications=True).all():
            members.append(member)
        return members


class LivePublicPayoutAccountMarkedIncomplete(LivePayoutAccountMarkedIncomplete):
    """
    A public payout account that is connected to a live crowdfunding campaign was marked incomplete
    """
    subject = pgettext('email', u'Incomplete payout account for running campaign')
    template = 'messages/platform_manager/live_public_payout_account_rejected'
