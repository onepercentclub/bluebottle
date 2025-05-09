from django.conf import settings
from django.utils.translation import gettext_lazy as _

from bluebottle.members.models import Member
from bluebottle.notifications.messages import TransitionMessage


class LivePayoutAccountMarkedIncomplete(TransitionMessage):
    subject = _(u'Live campaign identity verification failed!')
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
    subject = _(u'Incomplete payout account for running campaign')
    template = 'messages/platform_manager/live_public_payout_account_rejected'
