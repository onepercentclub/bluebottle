from django.utils.translation import gettext_lazy as _

from bluebottle.activities.states import (
    ActivityStateMachine, ContributorStateMachine, ContributionStateMachine
)
from bluebottle.fsm.state import (
    register, State, Transition, EmptyState, AllStates, ModelStateMachine
)
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, TimeContribution, DateActivitySlot, PeriodActivitySlot, SlotParticipant,
    TeamSlot,
)


class TimeBasedStateMachine(ActivityStateMachine):
    full = State(
        _('full'),
        'full',
        _('The number of people needed is reached and people can no longer register.')
    )

    lock = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
        ],
        full,
        name=_("Lock"),
        description=_(
            "People can no longer join the event. "
            "Triggered when the attendee limit is reached."
        )
    )
    unlock = Transition(
        full,
        ActivityStateMachine.open,
        name=_("Unlock"),
        description=_(
            "People can now join again. "
            "Triggered when the attendee number drops between the limit."
        )
    )

    reopen = Transition(
        full,
        ActivityStateMachine.open,
        name=_("Unlock"),
        description=_(
            "The number of participants has fallen below the required number. "
            "People can sign up again for the task."
        )
    )

    reopen_manually = Transition(
        [ActivityStateMachine.succeeded, ActivityStateMachine.expired],
        ActivityStateMachine.draft,
        name=_("Reopen"),
        permission=ActivityStateMachine.is_owner,
        automatic=False,
        description=_(
            "The number of participants has fallen below the required number. "
            "People can sign up again for the task."
        )
    )

    succeed = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.expired,
            full,
        ],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        description=_(
            'The activity ends and people can no longer register. '
            'Participants will keep their spent hours, '
            'but will no longer be allocated new hours.'),
        automatic=True,
    )

    cancel = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
            full,
        ],
        ActivityStateMachine.cancelled,
        name=_('Cancel'),
        description=_(
            'Cancel if the activity will not be executed. '
            'An activity manager can no longer edit the activity '
            'and it will no longer be visible on the platform. '
            'The activity will still be visible in the back office '
            'and will continue to count in the reporting.'
        ),
        automatic=False,
    )


@register(DateActivity)
class DateStateMachine(TimeBasedStateMachine):
    reschedule = Transition(
        [ActivityStateMachine.succeeded, ActivityStateMachine.expired],
        ActivityStateMachine.open,
        name=_("Reschedule"),
        permission=ActivityStateMachine.is_owner,
        automatic=True,
        description=_(
            "The activity is reopened because the start date changed."
        )
    )


@register(PeriodActivity)
class PeriodStateMachine(TimeBasedStateMachine):
    def can_succeed(self):
        return len(self.instance.active_participants) > 0

    succeed_manually = Transition(
        [ActivityStateMachine.open, TimeBasedStateMachine.full],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        automatic=False,
        description=_("Close this activity and allocate the hours to the participants."),
        conditions=[can_succeed],
        permission=ActivityStateMachine.is_owner,
    )

    reschedule = Transition(
        [
            ActivityStateMachine.expired,
            ActivityStateMachine.succeeded
        ],
        ActivityStateMachine.open,
        name=_("Reschedule"),
        description=_(
            "The date of the activity has been changed to a date in the future. "
            "The status of the activity will be recalculated."
        ),
    )


class ActivitySlotStateMachine(ModelStateMachine):

    draft = State(
        _('draft'),
        'draft',
        _('The slot is incomplete.')
    )

    open = State(
        _('open'),
        'open',
        _('The slot is accepting new participants.')
    )

    full = State(
        _('full'),
        'full',
        _('The number of people needed is reached and people can no longer register.')
    )

    running = State(
        _('running'),
        'running',
        _('The slot is currently taking place.')
    )

    finished = State(
        _('finished'),
        'finished',
        _('The slot has ended.')
    )

    cancelled = State(
        _('cancelled'),
        'cancelled',
        _('The slot is cancelled.')
    )

    def is_activity_owner(self, user):
        """Is manager of related activity"""
        return (
            user == self.instance.activity.owner or
            user == self.instance.activity.initiative.owner or
            user in self.instance.activity.initiative.activity_managers.all() or
            user.is_staff or
            user.is_superuser
        )

    initiate = Transition(
        EmptyState(),
        draft,
        name=_('Initiate'),
        description=_(
            'The slot was created.'
        ),
    )

    mark_complete = Transition(
        draft,
        open,
        name=_('Complete'),
        description=_(
            'The slot was completed.'
        ),
    )

    mark_incomplete = Transition(
        open,
        draft,
        name=_('Mark incomplete'),
        description=_(
            'The slot was made incomplete.'
        ),
    )

    cancel = Transition(
        AllStates(),
        cancelled,
        name=_('Cancel'),
        automatic=False,
        permission=is_activity_owner,
        description=_(
            'Cancel the slot. People can no longer apply. Contributions are not counted anymore.'
        ),
    )

    reopen = Transition(
        cancelled,
        open,
        name=_('Reopen'),
        description=_(
            'Reopen a cancelled slot. People can apply again. Contributions are counted again'
        ),
    )

    lock = Transition(
        open,
        full,
        name=_("Lock"),
        description=_(
            "People can no longer join the slot. "
            "Triggered when the attendee limit is reached."
        )
    )

    unlock = Transition(
        full,
        open,
        name=_("Unlock"),
        description=_(
            "The number of participants has fallen below the required number. "
            "People can sign up again for the slot."
        )
    )

    start = Transition(
        [open, finished, full],
        running,
        name=_("Start"),
        description=_(
            "The slot is currently taking place."
        )
    )
    finish = Transition(
        [open, running, full],
        finished,
        name=_("Finish"),
        description=_(
            "The slot has ended. "
            "Triggered when slot has ended."
        )
    )

    reschedule = Transition(
        [running, finished],
        open,
        name=_("Reschedule"),
        description=_(
            "Reopen the slot. "
            "Triggered when start of the slot is changed."
        )
    )


@register(DateActivitySlot)
class DateActivitySlotStateMachine(ActivitySlotStateMachine):
    pass


@register(PeriodActivitySlot)
class PeriodActivitySlotStateMachine(ActivitySlotStateMachine):
    pass


@register(TeamSlot)
class TeamSlotStateMachine(ActivitySlotStateMachine):
    initiate = Transition(
        EmptyState(),
        ActivitySlotStateMachine.open,
        name=_('Initiate'),
        description=_(
            'The slot was created.'
        ),
    )


class ParticipantStateMachine(ContributorStateMachine):
    new = State(
        _('pending'),
        'new',
        _("This person has applied and must be reviewed.")
    )
    accepted = State(
        _('participating'),
        'accepted',
        _('This person takes part in the activity.')
    )
    rejected = State(
        _('removed'),
        'rejected',
        _("This person's contribution is removed and the spent hours are reset to zero.")
    )
    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _('This person has withdrawn. Spent hours are retained.')
    )
    cancelled = State(
        _('cancelled'),
        'cancelled',
        _("The activity has been cancelled. This person's contribution "
          "is removed and the spent hours are reset to zero.")
    )

    def is_user(self, user):
        """is participant"""
        return self.instance.user == user

    def can_accept_participant(self, user):
        """can accept participant"""
        return (
            user in [
                self.instance.activity.owner,
                self.instance.activity.initiative.owner
            ] or
            (self.instance.team and self.instance.team.owner == user) or
            user.is_staff or
            user in self.instance.activity.initiative.activity_managers.all()
        )

    def can_reject_participant(self, user):
        """can accept participant"""
        return self.can_accept_participant(user) and not user == self.instance.user

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
            rejected
        ],
        accepted,
        name=_('Accept'),
        description=_("Accept this person as a participant to the Activity."),
        automatic=False,
        permission=can_accept_participant,
    )

    add = Transition(
        [
            ContributorStateMachine.new
        ],
        accepted,
        name=_('Add'),
        description=_("Add this person as a participant to the activity."),
        automatic=True
    )

    reject = Transition(
        [
            ContributorStateMachine.new,
        ],
        rejected,
        name=_('Reject'),
        description=_("Reject this person as a participant in the activity."),
        automatic=False,
        permission=can_reject_participant,
    )

    remove = Transition(
        [
            accepted,
        ],
        rejected,
        name=_('Remove'),
        description=_("Remove this person as a participant from the activity."),
        automatic=False,
        permission=can_reject_participant,
    )

    withdraw = Transition(
        [
            ContributorStateMachine.new,
            accepted
        ],
        withdrawn,
        name=_('Withdraw'),
        description=_("Stop your participation in the activity. "
                      "Any hours spent will be kept, but no new hours will be allocated."),
        automatic=False,
        permission=is_user,
        hide_from_admin=True,
    )

    reapply = Transition(
        withdrawn,
        ContributorStateMachine.new,
        name=_('Reapply'),
        description=_("User re-applies for the task after previously withdrawing."),
        automatic=False,
        conditions=[activity_is_open],
        permission=is_user,
    )


@register(DateParticipant)
class DateParticipantStateMachine(ParticipantStateMachine):
    pass


@register(PeriodParticipant)
class PeriodParticipantStateMachine(ParticipantStateMachine):
    def is_not_team(self):
        return not self.instance.team

    stopped = State(
        _('stopped'),
        'stopped',
        _('The participant (temporarily) stopped. Contributions will no longer be created.')
    )

    stop = Transition(
        ParticipantStateMachine.accepted,
        stopped,
        name=_('Stop'),
        permission=ParticipantStateMachine.can_accept_participant,
        description=_("Participant stopped contributing."),
        automatic=False,
        conditions=[ParticipantStateMachine.activity_is_open, is_not_team]
    )

    start = Transition(
        stopped,
        ParticipantStateMachine.accepted,
        name=_('Start'),
        permission=ParticipantStateMachine.can_accept_participant,
        description=_("Participant started contributing again."),
        automatic=False,
    )


@register(SlotParticipant)
class SlotParticipantStateMachine(ModelStateMachine):
    registered = State(
        _('registered'),
        'registered',
        _("This person registered to this slot.")
    )
    succeeded = State(
        _('succeeded'),
        'succeeded',
        _("The contribution was successful.")
    )
    removed = State(
        _('removed'),
        'removed',
        _('This person no longer takes part in this slot.')
    )
    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _('This person has withdrawn from this slot. Spent hours are retained.')
    )
    cancelled = State(
        _('cancelled'),
        'cancelled',
        _("The slot has been cancelled. This person's contribution "
          "is removed and the spent hours are reset to zero.")
    )

    def is_user(self, user):
        """is participant"""
        return self.instance.user == user

    def can_accept_participant(self, user):
        """can accept participant"""
        return (
            user in [
                self.instance.activity.owner,
                self.instance.activity.initiative.owner
            ] or
            user.is_staff or
            user in self.instance.activity.initiative.activity_managers.all()
        )

    def can_reject_participant(self, user):
        """can accept participant"""
        return self.can_accept_participant(user) and not user == self.instance.user

    def slot_is_open(self):
        """task is open"""
        return self.instance.slot.status in (
            DateActivitySlotStateMachine.open.value,
            DateActivitySlotStateMachine.running.value,
        )

    initiate = Transition(
        EmptyState(),
        registered,
        name=_('Initiate'),
        description=_("User registered to join the slot."),
    )

    accept = Transition(
        [removed, withdrawn, cancelled],
        registered,
        name=_('Accept'),
        description=_("Accept the previously person as a participant to the slot."),
        automatic=False,
        permission=can_accept_participant,
    )

    remove = Transition(
        registered,
        removed,
        name=_('Remove'),
        description=_("Remove this person as a participant from the slot."),
        automatic=False,
        permission=can_reject_participant,
    )

    withdraw = Transition(
        registered,
        withdrawn,
        name=_('Withdraw'),
        description=_("Stop your participation in the slot."),
        automatic=False,
        permission=is_user,
        hide_from_admin=True,
    )

    reapply = Transition(
        withdrawn,
        registered,
        name=_('Reapply'),
        description=_("User re-applies to the slot after previously withdrawing."),
        automatic=False,
        conditions=[slot_is_open],
        permission=is_user,
    )


@register(TimeContribution)
class TimeContributionStateMachine(ContributionStateMachine):
    pass
