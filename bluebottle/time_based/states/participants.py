from django.utils.translation import gettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributorStateMachine
from bluebottle.fsm.state import register, State, Transition, EmptyState
from bluebottle.time_based.effects.participant import CreateScheduleRegistrationEffect
from bluebottle.time_based.models import (
    DateParticipant,
    Participant,
    PeriodicParticipant,
    ScheduleParticipant,
)
from bluebottle.time_based.models import (
    DeadlineParticipant,
)
from bluebottle.time_based.states.states import TimeBasedStateMachine


def activity_is_open(instance):
    """task is open"""
    return instance.activity.status in (
        TimeBasedStateMachine.open.value,
        TimeBasedStateMachine.full.value,
    )


class ParticipantStateMachine(ContributorStateMachine):
    new = State(
        _("new"),
        "new",
        _("This participant is new and ready to participate once the slot starts."),
    )
    accepted = State(
        _("participating"), "accepted", _("This person takes part in the activity.")
    )
    rejected = State(
        _("rejected"),
        "rejected",
        _(
            "This person's contribution is rejected and the spent hours are reset to zero."
        ),
    )
    removed = State(
        _("removed"),
        "removed",
        _(
            "This person's contribution is removed and the spent hours are reset to zero."
        ),
    )
    withdrawn = State(
        _("withdrawn"),
        "withdrawn",
        _("This person has withdrawn. Spent hours are retained."),
    )
    cancelled = State(
        _("cancelled"),
        "cancelled",
        _(
            "The activity has been cancelled. This person's contribution "
            "is removed and the spent hours are reset to zero."
        ),
    )
    succeeded = State(
        _("succeeded"), "succeeded", _("This person hast successfully contributed.")
    )

    def is_user(self, user):
        """is participant"""
        return self.instance.user == user

    def can_accept_participant(self, user):
        """can accept participant"""
        return (
            user
            in [self.instance.activity.owner, self.instance.activity.initiative.owner]
            or (self.instance.team and self.instance.team.owner == user)
            or user.is_staff
            or user in self.instance.activity.initiative.activity_managers.all()
        )

    initiate = Transition(
        EmptyState(),
        ContributorStateMachine.new,
        name=_("Initiate"),
        description=_("User applied to join the task."),
    )

    add = Transition(
        [ContributorStateMachine.new],
        accepted,
        name=_("Add"),
        description=_("Add this person as a participant to the activity."),
        automatic=True,
    )

    succeed = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.failed,
            rejected,
            accepted,
        ],
        succeeded,
        name=_("Succeed"),
        description=_("This participant has completed their contribution."),
        automatic=False,
        permission=can_accept_participant,
    )

    remove = Transition(
        [accepted, succeeded],
        rejected,
        name=_("Remove"),
        passed_label=_("removed"),
        description=_("Remove this person as a participant from the activity."),
        automatic=False,
        permission=can_accept_participant,
    )

    withdraw = Transition(
        [ContributorStateMachine.new, succeeded, accepted],
        withdrawn,
        name=_("Withdraw"),
        passed_label=_("withdrawn"),
        description=_(
            "Cancel your participation in the activity. Participation hours will not be counted."
        ),
        automatic=False,
        permission=is_user,
        hide_from_admin=True,
    )

    reapply = Transition(
        withdrawn,
        ContributorStateMachine.new,
        name=_("Reapply"),
        passed_label=_("reapplied"),
        description=_("User re-applies for the activity after previously withdrawing."),
        description_front_end=_("Do you want to sign up for this activity again?"),
        automatic=False,
        conditions=[activity_is_open],
        permission=is_user,
    )

    cancel = Transition(
        [ContributorStateMachine.new, accepted, succeeded],
        cancelled,
        name=_("Cancel"),
        passed_label=_("cancelled"),
        description=_("Cancel the participant, because the activity was cancelled."),
        automatic=True,
    )


@register(DateParticipant)
class DateParticipantStateMachine(ParticipantStateMachine):
    pass


class RegistrationParticipantStateMachine(ParticipantStateMachine):
    accept = Transition(
        [
            ParticipantStateMachine.new,
        ],
        ParticipantStateMachine.succeeded,
        name=_("Accept"),
        description=_("Accept this person as a participant to the Activity."),
        passed_label=_("accepted"),
        automatic=True,
        conditions=[lambda instance: instance.registration.status == "accepted"],
    )

    reject = Transition(
        [
            ContributorStateMachine.new,
            ParticipantStateMachine.accepted,
            ParticipantStateMachine.succeeded,
        ],
        ParticipantStateMachine.rejected,
        name=_("Reject"),
        description=_("Reject this person as a participant in the activity."),
        automatic=True,
        conditions=[lambda instance: instance.registration.status == "rejected"],
    )

    restore = Transition(
        [
            ParticipantStateMachine.cancelled,
        ],
        ParticipantStateMachine.new,
        name=_("Restore"),
        description=_("Restore previously failed participant"),
        automatic=True,
        conditions=[
            lambda instance: instance.activity.status
            in [
                "open",
                "succeeded",
                "locked",
            ]
        ],
    )

    remove = Transition(
        [ParticipantStateMachine.new, ParticipantStateMachine.succeeded],
        ParticipantStateMachine.removed,
        name=_("Remove"),
        passed_label=_("removed"),
        description=_("Remove this person as a participant from the activity."),
        automatic=False,
        permission=ParticipantStateMachine.can_accept_participant,
    )

    readd = Transition(
        [
            ParticipantStateMachine.removed,
        ],
        ParticipantStateMachine.new,
        name=_("Re-add"),
        passed_label=_("re-added"),
        description=_("Re-add this person as a participant to the activity"),
        automatic=False,
        permission=ParticipantStateMachine.can_accept_participant,
    )


@register(DeadlineParticipant)
class DeadlineParticipantStateMachine(RegistrationParticipantStateMachine):

    add = Transition(
        [ContributorStateMachine.new],
        ParticipantStateMachine.succeeded,
        name=_("Add"),
        description=_("Add this person as a participant to the activity."),
        automatic=True,
    )


def participant_has_a_slot(instance):
    return instance.slot is not None


@register(ScheduleParticipant)
class ScheduleParticipantStateMachine(RegistrationParticipantStateMachine):

    @property
    def related_models(self):
        for participant in self.instance.contributions.all():
            yield participant

        yield self.instance.activity

    initiate = Transition(
        EmptyState(),
        ContributorStateMachine.new,
        name=_("Initiate"),
        description=_("User applied to join the task."),
        effects=[CreateScheduleRegistrationEffect],
    )
    accepted = State(
        _("unscheduled"),
        "accepted",
        _("This person takes part in the activity, but needs to be assigned a slot."),
    )
    scheduled = State(_("scheduled"), "scheduled", _("This person is assigned a slot."))

    cancel = Transition(
        [
            ContributorStateMachine.new,
            RegistrationParticipantStateMachine.accepted,
            RegistrationParticipantStateMachine.succeeded,
            scheduled,
        ],
        RegistrationParticipantStateMachine.cancelled,
        name=_("Cancel"),
        passed_label=_("cancelled"),
        description=_("Cancel the participant, because the activity was cancelled."),
        automatic=True,
        conditions=[
            lambda instance: instance.activity.status
            == ActivityStateMachine.cancelled.value
        ],
    )

    accept = Transition(
        [
            ParticipantStateMachine.new,
            ParticipantStateMachine.rejected,
        ],
        ParticipantStateMachine.accepted,
        name=_("Accept"),
        description=_("Accept this person as a participant to the Activity."),
        passed_label=_("accepted"),
        automatic=True,
        conditions=[
            lambda instance: instance.registration
            and instance.registration.status == "accepted"
        ],
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
        description=_("Reject this person as a participant in the activity."),
        automatic=True,
        conditions=[
            lambda instance: instance.registration
            and instance.registration.status == "rejected"
        ],
    )

    remove = Transition(
        [
            ParticipantStateMachine.new,
            ParticipantStateMachine.succeeded,
            scheduled,
        ],
        ParticipantStateMachine.removed,
        name=_("Remove"),
        passed_label=_("removed"),
        description=_("Remove this person as a participant from the activity."),
        automatic=False,
        permission=ParticipantStateMachine.can_accept_participant,
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
        ],
        scheduled,
        name=_("Schedule"),
        description=_("Schedule this participant the Activity."),
        passed_label=_("scheduled"),
        automatic=True,
        conditions=[lambda instance: instance.slot_id is not None],
    )

    unschedule = Transition(
        [scheduled],
        ParticipantStateMachine.accepted,
        name=_("Unschedule"),
        description=_("Unchedule this participant the Activity."),
        passed_label=_("unscheduled"),
        automatic=True,
        conditions=[lambda instance: instance.slot_id is None],
    )

    succeed = Transition(
        [scheduled],
        ParticipantStateMachine.succeeded,
        name=_("Succeed"),
        description=_("Succeed participant."),
        passed_label=_("succeeded"),
        automatic=True,
        conditions=[
            lambda instance: instance.slot_id and instance.slot.status == "finished"
        ],
    )

    reset = Transition(
        [ParticipantStateMachine.succeeded],
        ParticipantStateMachine.new,
        name=_("Reset"),
        description=_("Reset participant."),
        passed_label=_("Reset"),
        automatic=True,
        conditions=[
            lambda instance: instance.slot_id is None
            or instance.slot.status != "finished"
        ],
    )


@register(PeriodicParticipant)
class PeriodicParticipantStateMachine(RegistrationParticipantStateMachine):
    pass
