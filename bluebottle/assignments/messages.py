from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class ApplicantAcceptedMessage(TransitionMessage):
    subject = _('You have been accepted for the assignment!')
    template = 'messages/applicant_accepted'


class ApplicantRejectedMessage(TransitionMessage):
    subject = _('You not been selected for the assignment')
    template = 'messages/applicant_reject4d'
