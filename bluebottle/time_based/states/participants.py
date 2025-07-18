from django.utils.translation import gettext_lazy as _

from bluebottle.activities.states import ContributorStateMachine
from bluebottle.fsm.state import register, State, Transition, EmptyState
from bluebottle.time_based.models import (
    DateParticipant,
    PeriodicParticipant, ScheduleParticipant, TeamScheduleParticipant, RegisteredDateParticipant
)
from bluebottle.time_based.models import (
    DeadlineParticipant,
)
from bluebottle.time_based.states.states import TimeBasedStateMachine


class ParticipantStateMachine(ContributorStateMachine):
    new = State(
        _("Pending"),
        "new",
        _("This participant is new and will waiting for the registration to be accepted."),
    )
    accepted = State(
        _('Participating'),
        'accepted',
        _('This person takes part in the activity.')
    )
    rejected = State(
        _('Rejected'),
        'rejected',
        _("This person's contribution is rejected and the spent hours are reset to zero.")
    )
    removed = State(
        _('Removed'),
        'removed',
        _("This person's contribution is removed and the spent hours are reset to zero.")
    )
    withdrawn = State(
        _('Withdrawn'),
        'withdrawn',
        _('This person has withdrawn. Spent hours are retained.')
    )
    cancelled = State(
        _('Cancelled'),
        'cancelled',
        _("The activity has been cancelled. This person's contribution "
          "is removed and the spent hours are reset to zero.")
    )
    succeeded = State(
        _('Succeeded'),
        'succeeded',
        _('This person hast successfully contributed.')
    )

    def is_user(self, user):
        """is participant"""
        return self.instance.user == user

    def can_accept_participant(self, user):
        """can accept participant"""
        return (
            user in self.instance.activity.owners or
            user.is_staff or
            user.is_superuser
        )

    def activity_is_open(self):
        """task is open"""
        return self.instance.activity.status in (
            TimeBasedStateMachine.open.value,
            TimeBasedStateMachine.full.value
        )

    initiate = Transition(
        EmptyState(),
        ContributorStateMachine.new,
        name=_('Initiate'),
        description=_("User applied to join the task."),
    )

    accept = Transition(
        [
            ContributorStateMachine.new,
            withdrawn,
            removed,
            rejected
        ],
        accepted,
        name=_('Accept'),
        description=_("Accept this person as a participant of this Activity."),
        passed_label=_('accepted'),
        permission=can_accept_participant,
        automatic=False,
    )

    add = Transition(
        [
            ContributorStateMachine.new
        ],
        accepted,
        name=_('Add'),
        description=_("Add this person as a participant of this activity."),
        automatic=True
    )

    reject = Transition(
        [ContributorStateMachine.new, accepted, succeeded],
        rejected,
        name=_("Reject"),
        description=_("Reject this person as a participant of this activity."),
        automatic=False,
        permission=can_accept_participant,
    )

    succeed = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.failed,
            rejected,
            accepted
        ],
        succeeded,
        name=_('Succeed'),
        description=_("This participant has completed their contribution."),
        automatic=False,
        permission=can_accept_participant,
    )

    remove = Transition(
        [
            new,
            accepted,
            succeeded
        ],
        removed,
        name=_('Remove'),
        passed_label=_('removed'),
        description=_("Remove this person as a participant of this activity."),
        automatic=False,
        permission=can_accept_participant,
    )

    auto_remove = Transition(
        [
            new,
            accepted,
            succeeded,
        ],
        removed,
        name=_('Auto remove'),
        passed_label=_('removed'),
        description=_("Remove this person because a parent object was removed."),
        automatic=True,
    )

    withdraw = Transition(
        [
            ContributorStateMachine.new,
            succeeded,
            accepted
        ],
        withdrawn,
        name=_('Withdraw'),
        passed_label=_('withdrawn'),
        description=_("Cancel your participation in the activity. Participation hours will not be counted."),
        automatic=False,
        permission=is_user,
        hide_from_admin=True,
    )

    reapply = Transition(
        withdrawn,
        ContributorStateMachine.new,
        name=_('Reapply'),
        passed_label=_('reapplied'),
        description=_("User re-applies for the activity after previously withdrawing."),
        description_front_end=_("Do you want to sign up for this activity again?"),
        automatic=False,
        conditions=[activity_is_open],
        permission=is_user,
    )

    cancel = Transition(
        [
            ContributorStateMachine.new,
            accepted,
            succeeded,
        ],
        cancelled,
        name=_('Cancel'),
        passed_label=_('cancelled'),
        description=_("Cancel the participant, because the activity was cancelled."),
        automatic=True,
    )

    restore = Transition(
        cancelled,
        accepted,
        name=_('Restore'),
        passed_label=_('restored'),
        description=_("Restore the participant, because the activity was restored."),
        automatic=True,
    )


class RegistrationParticipantStateMachine(ParticipantStateMachine):
    accept = Transition(
        [
            ParticipantStateMachine.new,
            ParticipantStateMachine.rejected,
            ParticipantStateMachine.removed,
            ParticipantStateMachine.withdrawn,
            ParticipantStateMachine.succeeded,
        ],
        ParticipantStateMachine.accepted,
        name=_("Accept"),
        description=_("Accept this person as a participant of this activity."),
        passed_label=_("accepted"),
        automatic=True,
    )

    reject = Transition(
        [
            ContributorStateMachine.new,
            ParticipantStateMachine.accepted,
            ParticipantStateMachine.succeeded,
        ],
        ParticipantStateMachine.rejected,
        name=_("Reject"),
        description=_("Reject this person as a participant of this activity."),
        automatic=True,
    )

    restore = Transition(
        ParticipantStateMachine.cancelled,
        ParticipantStateMachine.accepted,
        name=_("Restore"),
        description=_("Restore previously cancelled participant"),
        automatic=True,
    )

    succeed = Transition(
        [
            ParticipantStateMachine.new,
            ParticipantStateMachine.accepted,
            ParticipantStateMachine.failed,
        ],
        ParticipantStateMachine.succeeded,
        name=_('Succeed'),
        description=_("This participant has completed their contribution."),
        automatic=True,
    )

    remove = Transition(
        [
            ParticipantStateMachine.new,
            ParticipantStateMachine.accepted,
            ParticipantStateMachine.succeeded
        ],
        ParticipantStateMachine.removed,
        name=_('Remove'),
        passed_label=_('removed'),
        description=_("Remove this person as a participant of this activity."),
        automatic=False,
        permission=ParticipantStateMachine.can_accept_participant,
    )

    auto_remove = Transition(
        [
            ParticipantStateMachine.new,
            ParticipantStateMachine.accepted,
            ParticipantStateMachine.succeeded
        ],
        ParticipantStateMachine.removed,
        name=_('Auto remove'),
        passed_label=_('removed'),
        description=_("Remove this person as a participant because a parent object has been removed."),
        automatic=True,
    )

    readd = Transition(
        [
            ParticipantStateMachine.removed,
            ParticipantStateMachine.cancelled,
        ],
        ParticipantStateMachine.accepted,
        name=_("Re-add"),
        passed_label=_("re-added"),
        description=_("Re-add this person as a participant of this activity"),
        automatic=False,
        permission=ParticipantStateMachine.can_accept_participant,
    )


@register(DeadlineParticipant)
class DeadlineParticipantStateMachine(RegistrationParticipantStateMachine):
    add = Transition(
        [ContributorStateMachine.new],
        ParticipantStateMachine.accepted,
        name=_("Add"),
        description=_("Add this person as a participant of this activity."),
        automatic=True,
    )


@register(RegisteredDateParticipant)
class RegisteredDateParticipantStateMachine(RegistrationParticipantStateMachine):
    add = Transition(
        [ContributorStateMachine.new],
        ParticipantStateMachine.accepted,
        name=_("Add"),
        description=_("Add this person as a participant of this activity."),
        automatic=True,
    )
    restore = Transition(
        ParticipantStateMachine.cancelled,
        ParticipantStateMachine.succeeded,
        name=_("Restore"),
        description=_("Restore previously cancelled participant"),
        automatic=True,
    )
    readd = Transition(
        [
            ParticipantStateMachine.removed,
        ],
        ParticipantStateMachine.succeeded,
        name=_("Re-add"),
        description=_("Add previously removed participant"),
    )


@register(ScheduleParticipant)
class ScheduleParticipantStateMachine(RegistrationParticipantStateMachine):
    def participant_has_a_slot(self):
        return self.instance.slot is not None

    accepted = State(
        _("Unscheduled"),
        "accepted",
        _("This person takes part in the activity, but needs to be assigned a slot."),
    )
    scheduled = State(_("Scheduled"), "scheduled", _("This person is assigned a slot."))

    accept = Transition(
        [
            ParticipantStateMachine.new,
            ParticipantStateMachine.rejected,
            ParticipantStateMachine.removed,
        ],
        ParticipantStateMachine.accepted,
        name=_("Accept"),
        description=_("Accept this person as a participant of this Activity."),
        passed_label=_("accepted"),
        automatic=True,
    )

    reject = Transition(
        [
            ContributorStateMachine.new,
            RegistrationParticipantStateMachine.accepted,
            RegistrationParticipantStateMachine.succeeded,
            scheduled,
        ],
        RegistrationParticipantStateMachine.rejected,
        name=_("Reject"),
        description=_("Reject this person as a participant of this activity."),
        automatic=True,
    )

    remove = Transition(
        [
            ParticipantStateMachine.new,
            RegistrationParticipantStateMachine.accepted,
            ParticipantStateMachine.succeeded,
            scheduled,
        ],
        ParticipantStateMachine.removed,
        name=_("Remove"),
        passed_label=_("removed"),
        description=_("Remove this person as a participant of this activity."),
        automatic=False,
        permission=ParticipantStateMachine.can_accept_participant,
    )

    auto_remove = Transition(
        [
            ParticipantStateMachine.new,
            RegistrationParticipantStateMachine.accepted,
            ParticipantStateMachine.succeeded,
            scheduled,
        ],
        ParticipantStateMachine.removed,
        name=_("Auto remove"),
        passed_label=_("removed"),
        description=_("Remove this person as a participant because a parent object got removed."),
        automatic=True,
    )

    withdraw = Transition(
        [
            ContributorStateMachine.new,
            RegistrationParticipantStateMachine.succeeded,
            RegistrationParticipantStateMachine.accepted,
            scheduled,
        ],
        RegistrationParticipantStateMachine.withdrawn,
        name=_("Withdraw"),
        passed_label=_("withdrawn"),
        description=_(
            "Cancel your participation in the activity. Participation hours will not be counted."
        ),
        automatic=False,
        permission=RegistrationParticipantStateMachine.is_user,
        hide_from_admin=True,
    )

    schedule = Transition(
        [
            ParticipantStateMachine.new,
            ParticipantStateMachine.accepted,
            ParticipantStateMachine.cancelled,
            ParticipantStateMachine.succeeded,
        ],
        scheduled,
        name=_("Schedule"),
        description=_("Schedule this participant the Activity."),
        passed_label=_("Scheduled"),
        automatic=True,
    )

    unschedule = Transition(
        [
            scheduled,
            ParticipantStateMachine.succeeded,
        ],
        ParticipantStateMachine.accepted,
        name=_("Unschedule"),
        description=_("Unschedule this participant."),
        passed_label=_("unscheduled"),
        automatic=True,
    )

    succeed = Transition(
        [
            scheduled,
            ParticipantStateMachine.new,
            ParticipantStateMachine.accepted,
            ParticipantStateMachine.cancelled
        ],
        ParticipantStateMachine.succeeded,
        name=_("Succeed"),
        description=_("Succeed this participant for the Activity."),
        passed_label=_("succeeded"),
        automatic=True,
    )

    reset = Transition(
        ParticipantStateMachine.succeeded,
        scheduled,
        name=_("Reset"),
        description=_("Reset participant to scheduled"),
        passed_label=_("reset"),
        automatic=True,
    )
    cancel = Transition(
        [
            ParticipantStateMachine.new,
            ParticipantStateMachine.accepted,
            ParticipantStateMachine.succeeded,
            scheduled
        ],
        ParticipantStateMachine.cancelled,
        name=_('Cancel'),
        passed_label=_('cancelled'),
        description=_("Cancel the participant, because the activity was cancelled."),
        automatic=True,
    )


@register(TeamScheduleParticipant)
class TeamScheduleParticipantStateMachine(ScheduleParticipantStateMachine):
    initiate = Transition(
        EmptyState(),
        ScheduleParticipantStateMachine.new,
        name=_('Initiate'),
        description=_("Member signs up for team"),
    )

    withdraw = Transition(
        [
            ScheduleParticipantStateMachine.new,
            ScheduleParticipantStateMachine.accepted,
            ScheduleParticipantStateMachine.scheduled,
        ],
        ScheduleParticipantStateMachine.withdrawn,
        name=_("Withdraw"),
        automatic=False,
        hide_from_admin=True,
        permission=RegistrationParticipantStateMachine.is_user,
        description=_("Participant withdraws from the team slot."),
        passed_label=_("withdrawn"),
    )

    reapply = Transition(
        ScheduleParticipantStateMachine.withdrawn,
        ScheduleParticipantStateMachine.new,
        name=_("Reapply"),
        automatic=False,
        hide_from_admin=True,
        permission=RegistrationParticipantStateMachine.is_user,
        description=_("Participant joins the team slot."),
    )


@register(PeriodicParticipant)
class PeriodicParticipantStateMachine(RegistrationParticipantStateMachine):
    pass


@register(DateParticipant)
class DateParticipantStateMachine(RegistrationParticipantStateMachine):

    finish = Transition(
        RegistrationParticipantStateMachine.accepted,
        RegistrationParticipantStateMachine.succeeded,
        automatic=True,
        name=_('Finish'),
        description="Slot has finished"
    )

    def activity_is_open(self):
        """task is open"""
        return self.instance.slot_id and self.instance.slot.status in (
            'open',
            'running',
        )
