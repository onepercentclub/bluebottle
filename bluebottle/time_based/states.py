from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import (
    ActivityStateMachine, ContributorStateMachine, ContributionStateMachine
)
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, TimeContribution,
)
from bluebottle.fsm.state import register, State, Transition, EmptyState


class TimeBasedStateMachine(ActivityStateMachine):
    full = State(
        _('full'),
        'full',
        _('The number of people needed is reached and people can no longer register.')
    )
    running = State(
        _('running'),
        'running',
        _('The activity is taking place and people can\'t participate any more.')
    )

    lock = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
            running
        ],
        full,
        name=_("Lock"),
        description=_(
            "People can no longer join the event. "
            "Triggered when the attendee limit is reached."
        )
    )

    reopen = Transition(
        [running, full],
        ActivityStateMachine.open,
        name=_("Reopen"),
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
            running
        ],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        description=_(
            'The activity ends and people can no longer register. '
            'Participants will keep their spent hours, '
            'but will no longer be allocated new hours.'),
        automatic=True,
    )

    start = Transition(
        [
            ActivityStateMachine.open,
            full
        ],
        running,
        name=_("Start"),
        description=_("Start the event.")
    )

    cancel = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
            full,
            running
        ],
        ActivityStateMachine.cancelled,
        name=_('Cancel'),
        description=_(
            'Cancel if the activity will not be executed. '
            'The activity manager can no longer edit the activity '
            'and it will no longer be visible on the platform. '
            'The activity will still be visible in the back office '
            'and will continue to count in the reporting.'
        ),
        automatic=False,
    )


@register(DateActivity)
class DateStateMachine(TimeBasedStateMachine):
    reschedule = Transition(
        [
            TimeBasedStateMachine.running,
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


@register(PeriodActivity)
class PeriodStateMachine(TimeBasedStateMachine):
    def can_succeed(self):
        return self.instance.duration_period != 'overall' and len(self.instance.active_participants) > 0

    succeed_manually = Transition(
        [ActivityStateMachine.open, TimeBasedStateMachine.full, TimeBasedStateMachine.running],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        automatic=False,
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
        return user in [
            self.instance.activity.owner,
            self.instance.activity.initiative.activity_manager,
            self.instance.activity.initiative.owner
        ] or user.is_staff

    def can_reject_participant(self, user):
        """can accept participant"""
        return self.can_accept_participant(user) and not user == self.instance.user

    def activity_is_open(self):
        """task is open"""
        return self.instance.activity.status == ActivityStateMachine.open.value

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
            ContributorStateMachine.accepted,
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
        permission=ContributorStateMachine.is_user,
    )


@register(DateParticipant)
class DateParticipantStateMachine(ParticipantStateMachine):
    pass


@register(PeriodParticipant)
class PeriodParticipantStateMachine(ParticipantStateMachine):
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
        conditions=[ParticipantStateMachine.activity_is_open]
    )

    start = Transition(
        stopped,
        ParticipantStateMachine.accepted,
        name=_('Start'),
        permission=ParticipantStateMachine.can_accept_participant,
        description=_("Participant started contributing again."),
        automatic=False,
    )


@register(TimeContribution)
class TimeContributionStateMachine(ContributionStateMachine):
    pass
