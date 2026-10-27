from django.utils.translation import gettext_lazy as _

from bluebottle.utils.forms import TransitionConfirmationForm


class RegistrationRejectForm(TransitionConfirmationForm):
    title = _('Reject registration')

    @classmethod
    def message_class(cls):
        from bluebottle.time_based.messages.registrations import UserRegistrationRejectedNotification
        return UserRegistrationRejectedNotification


class RegistrationAcceptForm(TransitionConfirmationForm):
    title = _('Accept registration')

    @classmethod
    def message_class(cls):
        from bluebottle.time_based.messages.registrations import UserRegistrationAcceptedNotification
        return UserRegistrationAcceptedNotification
