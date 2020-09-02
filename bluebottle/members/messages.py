# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from bluebottle.notifications.messages import TransitionMessage


class AccountActivationMessage(TransitionMessage):
    subject = _('Welcome to {site_name}!')
    template = 'messages/account_activation'

    def get_recipients(self):
        yield self.obj


class SignUptokenMessage(TransitionMessage):
    subject = _('Your activation link for {site_name}')
    template = 'messages/sign_up_token'

    def get_recipients(self):
        yield self.obj
