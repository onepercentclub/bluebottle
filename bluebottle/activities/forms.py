from django import forms
from django.utils.translation import gettext_lazy as _

from bluebottle.utils.forms import TransitionConfirmationForm


class ImpactReminderConfirmationForm(forms.Form):
    title = _('Send impact reminder message')


class ActivityRejectedForm(TransitionConfirmationForm):
    title = _('Activity rejected')

    @classmethod
    def message_class(cls):
        from bluebottle.activities.messages.activity_manager import ActivityRejectedNotification
        return ActivityRejectedNotification


class ActivityAcceptedForm(TransitionConfirmationForm):
    title = _('Activity accepted')

    @classmethod
    def message_class(cls):
        from bluebottle.activities.messages.activity_manager import ActivityApprovedNotification
        return ActivityApprovedNotification


class ActivityNeedsWorkForm(TransitionConfirmationForm):
    title = _('Activity needs work')

    @classmethod
    def message_class(cls):
        from bluebottle.activities.messages.activity_manager import ActivityNeedsWorkNotification
        return ActivityNeedsWorkNotification
