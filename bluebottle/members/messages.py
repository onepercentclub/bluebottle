# -*- coding: utf-8 -*-
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import int_to_base36
from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage


class AccountActivationMessage(TransitionMessage):
    subject = pgettext('platform-email', u'Welcome to {site_name}!')
    template = 'messages/account_activation'

    def get_recipients(self):
        yield self.obj


class SignUpTokenMessage(TransitionMessage):
    subject = pgettext('platform-email', u'Activate your account for {site_name}')
    template = 'messages/sign_up_token'

    def get_recipients(self):
        yield self.obj


class PasswordResetMessage(TransitionMessage):
    subject = pgettext('platform-email', u'Password reset for {site_name}')
    template = 'messages/password_reset'

    def get_recipients(self):
        return [self.obj]

    def get_context(self, recipient):
        context = super().get_context(recipient)
        context.update({
            'uid': int_to_base36(self.obj.pk),
            'token': default_token_generator.make_token(self.obj),
        })
        return context
