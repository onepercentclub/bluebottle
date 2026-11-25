# -*- coding: utf-8 -*-
from django.utils.http import int_to_base36
from django.utils.translation import pgettext_lazy as pgettext

from bluebottle.notifications.messages import TransitionMessage
from bluebottle.members.tokens import password_reset_token_generator


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
            'token': password_reset_token_generator.make_token(self.obj),
        })
        return context
