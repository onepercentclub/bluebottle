from django.utils.translation import gettext_lazy as _

from bluebottle.activities.states import (
    ActivityStateMachine, ContributorStateMachine, ContributionStateMachine
)
from bluebottle.fsm.state import (
    register, State, Transition, EmptyState, ModelStateMachine
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
        passed_label=_('unlocked'),
        description=_(
            "The number of participants has fallen below the required number. "
            "People can sign up again for the task."
        )
    )

    reopen_manually = Transition(
        [ActivityStateMachine.succeeded, ActivityStateMachine.expired],
        ActivityStateMachine.draft,
        name=_("Reopen"),
        passed_label=_('reopened'),
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
            'It will no longer be visible on the platform. '
            'Contributions will not be counted in reporting.'
        ),
        description_front_end=_(
            'The activity will not be executed. Any contributions will be cancelled too.'
        ),
        passed_label=_('cancelled'),
        automatic=False,
        permission=ActivityStateMachine.is_owner,
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

    submit = None

    publish = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
        ],
        ActivityStateMachine.open,
        description=_('Publish your activity and let people participate.'),
        automatic=False,
        name=_('Publish'),
        passed_label=_('published'),
        permission=ActivityStateMachine.is_owner,
        conditions=[
            ActivityStateMachine.is_complete,
            ActivityStateMachine.is_valid,
            ActivityStateMachine.initiative_is_approved
        ],
    )

    auto_publish = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
        ],
        ActivityStateMachine.open,
        description=_('Automatically publish activity when initiative is approved'),
        automatic=False,
        name=_('Auto-publish'),
        conditions=[
            ActivityStateMachine.is_complete,
            ActivityStateMachine.is_valid,
        ],
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
        _('succeeded'),
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
        [open, finished, full],
        cancelled,
        name=_('Cancel'),
        automatic=False,
        permission=is_activity_owner,
        description=_(
            'This time slot will not take place. People can no longer join and contributions will not be counted.'
        ),
    )

    reopen = Transition(
        cancelled,
        open,
        name=_('Reopen'),
        automatic=False,
        description=_(
            'Reopen a cancelled slot. People can apply again. Contributions are counted again'
        ),
        description_front_end=_(
            "Reopening a time slot will allow people to join again and their contributions will be counted."
        )
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
        _('rejected'),
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
            rejected
        ],
        accepted,
        name=_('Accept'),
        description=_("Accept this person as a participant to the Activity."),
        passed_label=_('accepted'),
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
            accepted
        ],
        rejected,
        name=_('Reject'),
        description=_("Reject this person as a participant in the activity."),
        automatic=False,
        permission=can_accept_participant,
    )

    remove = Transition(
        [
            accepted,
        ],
        rejected,
        name=_('Remove'),
        passed_label=_('removed'),
        description=_("Remove this person as a participant from the activity."),
        automatic=False,
        permission=can_accept_participant,
    )

    withdraw = Transition(
        [
            ContributorStateMachine.new,
            accepted
        ],
        withdrawn,
        name=_('Withdraw'),
        passed_label=_('withdrawn'),
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
        passed_label=_('reapplied'),
        description=_("User re-applies for the activity after previously withdrawing."),
        description_front_end=_("Do you want to sign up for this activity again?"),
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
        _("This person registered.")
    )
    succeeded = State(
        _('succeeded'),
        'succeeded',
        _("The contribution was successful.")
    )
    removed = State(
        _('removed'),
        'removed',
        _('This person no longer takes part.')
    )
    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _('This person has withdrawn. Spent hours are retained.')
    )
    cancelled = State(
        _('cancelled'),
        'cancelled',
        _("The contribution was cancelled. This person's contribution "
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

    def slot_is_open(self):
        """task is open"""
        return self.instance.slot_id and self.instance.slot.status in (
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
        passed_label=_('accepted'),
        description=_("Accept the previously rejected person as a participant."),
        description_front_end=_("Do you want to accept this person as a participant?"),
        automatic=False,
        permission=can_accept_participant,
    )

    remove = Transition(
        registered,
        removed,
        name=_('Remove'),
        passed_label=_('removed'),
        description=_("Remove this person as a participant."),
        automatic=False,
        permission=can_accept_participant,
    )

    withdraw = Transition(
        registered,
        withdrawn,
        name=_('Withdraw'),
        passed_label=_('withdrawn'),
        description=_("Cancel the participation."),
        description_front_end=_(
            "You will no longer participate in this time slot. "
            "You can rejoin as long as the activity is open."
        ),
        automatic=False,
        permission=is_user,
        hide_from_admin=True,
    )

    reapply = Transition(
        withdrawn,
        registered,
        name=_('Reapply'),
        passed_label=_('reapplied'),
        description=_("User re-applies after previously withdrawing."),
        description_front_end=_(
            "Do you want to join this time slot again?"
        ),
        automatic=False,
        conditions=[slot_is_open],
        permission=is_user,
    )


@register(TimeContribution)
class TimeContributionStateMachine(ContributionStateMachine):
    pass
