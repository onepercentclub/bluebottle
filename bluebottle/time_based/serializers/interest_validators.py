from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from bluebottle.time_based.models import DateParticipant

ACTIVE_REGISTRATION_STATUSES = (
    'new',
    'accepted',
    'succeeded',
    'scheduled',
    'participating',
)
ACTIVE_PARTICIPANT_STATUSES = (
    'new',
    'accepted',
    'succeeded',
    'running',
)


class ActiveSlotParticipantValidator:
    def is_involved(self, user, slot):
        return DateParticipant.objects.filter(
            user=user,
            slot=slot,
            status__in=ACTIVE_PARTICIPANT_STATUSES,
        ).exists()


class ActiveRegistrationValidator:
    def is_involved(self, user, activity):
        return activity.registrations.filter(
            user=user,
            status__in=ACTIVE_REGISTRATION_STATUSES,
        ).exists()


class ActiveActivityParticipantValidator:
    def is_involved(self, user, activity):
        return activity.participants.filter(
            user=user,
            status__in=ACTIVE_PARTICIPANT_STATUSES,
        ).exists()


class UserAlreadyInvolvedValidator:
    message = _('You are already participating in or applied to this activity.')
    code = 'already_involved'

    def __init__(
        self,
        slot_participant_validator=None,
        registration_validator=None,
        activity_participant_validator=None,
    ):
        self.slot_participant_validator = (
            slot_participant_validator or ActiveSlotParticipantValidator()
        )
        self.registration_validator = (
            registration_validator or ActiveRegistrationValidator()
        )
        self.activity_participant_validator = (
            activity_participant_validator or ActiveActivityParticipantValidator()
        )

    def is_involved(self, user, activity, slot=None):
        if slot:
            return self.slot_participant_validator.is_involved(user, slot)

        if self.registration_validator.is_involved(user, activity):
            return True

        return self.activity_participant_validator.is_involved(user, activity)

    def validate(self, user, activity, slot=None):
        if self.is_involved(user, activity, slot):
            raise ValidationError(self.message, code=self.code)
