from django import forms
from django.utils.translation import gettext_lazy as _

from bluebottle.utils.forms import TransitionConfirmationForm


class ImpactReminderConfirmationForm(forms.Form):
    title = _('Send impact reminder message')


class ActivityRejectedForm(TransitionConfirmationForm):
    title = _('Activity rejected')

    custom_message = forms.CharField(
        widget=forms.Textarea,
        label=_('Custom message'),
        required=False,
        help_text=_(
            'You can provide a custom message to the activity manager explaining why their activity was rejected.'),
    )

    @staticmethod
    def get_message_class():
        from bluebottle.activities.messages.activity_manager import ActivityRejectedNotification
        return ActivityRejectedNotification

    def save(self, **kwargs):
        """
        Save the form data and return the custom message if provided.
        """
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None


class ActivityAcceptedForm(TransitionConfirmationForm):
    title = _('Activity accepted')

    custom_message = forms.CharField(
        widget=forms.Textarea,
        label=_('Custom message'),
        required=False,
        help_text=_(
            'You can provide a custom message to the activity manager to tell them that their activity was accepted and to tell them what the next steps will be.'),
    )

    @staticmethod
    def get_message_class():
        from bluebottle.activities.messages.activity_manager import ActivityApprovedNotification
        return ActivityApprovedNotification

    def save(self, **kwargs):
        """
        Save the form data and return the custom message if provided.
        """
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None


class ActivityNeedsWorkForm(TransitionConfirmationForm):
    title = _('Activity needs work')

    custom_message = forms.CharField(
        widget=forms.Textarea,
        label=_('Custom message'),
        required=False,
        help_text=_(
            'You can provide a custom message to the activity manager to tell them that their activity needs changes accepted'),
    )

    @staticmethod
    def get_message_class():
        from bluebottle.activities.messages.activity_manager import ActivityNeedsWorkNotification
        return ActivityNeedsWorkNotification

    def save(self, **kwargs):
        """
        Save the form data and return the custom message if provided.
        """
        if self.cleaned_data.get('custom_message'):
            self.transition.custom_message = self.cleaned_data['custom_message']
        return None
