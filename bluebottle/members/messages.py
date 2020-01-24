# -*- coding: utf-8 -*-
from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class AccountActivationMessage(TransitionMessage):
    subject = _(u"Welcome to {site_name}!")
    template = 'messages/account_activation'

    def get_recipients(self):
        return [self.obj]
