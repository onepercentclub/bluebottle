# -*- coding: utf-8 -*-
from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class AccountActivationMessage(TransitionMessage):
    subject = pgettext('email', u'Welcome to {site_name}!')
    template = 'messages/account_activation'

    def get_recipients(self):
        yield self.obj


class SignUpTokenMessage(TransitionMessage):
    subject = pgettext('email', u'Activate your account for {site_name}')
    template = 'messages/sign_up_token'

    def get_recipients(self):
        yield self.obj
