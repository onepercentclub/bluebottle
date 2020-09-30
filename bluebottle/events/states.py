from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine
from bluebottle.events.models import Event, Participant
from bluebottle.fsm.state import State, EmptyState, Transition, register


@register(Event)
class EventStateMachine(ActivityStateMachine):

    full = State(_('full'), 'full', _('Submit the activity for approval.'))
    running = State(
        _('running'),
        'running',
        _('The event is taking place and people can\'t join any more.')
    )

    cancel = Transition(
        [
            ActivityStateMachine.open,
            running,
            full,
            ActivityStateMachine.succeeded,
        ],
        ActivityStateMachine.cancelled,
        name=_('Cancel'),
        description=_(
            'Cancel if the event will not be executed. The activity manager will not be '
            'able to edit the event and it won\'t show up on the search page in the front end. '
            'The event will still be available in the back office and appear in your reporting.'
        ),
        automatic=False,
    )

    lock = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded
        ],
        full,
        name=_("Lock"),
        description=_(
            "People can no longer join the event. Triggered when the attendee limit is reached."
        )
    )

    reopen = Transition(
        full,
        ActivityStateMachine.open,
        name=_("Reopen"),
        description=_(
            "People can join the event again. Triggered when the number of attendees become "
            "less than the attendee limit."
        )
    )

    reschedule = Transition(
        [
            running,
            ActivityStateMachine.cancelled,
            ActivityStateMachine.succeeded
        ],
        ActivityStateMachine.open,
        name=_("Reschedule"),
        description=_("People can join the event again, because the date has changed."),
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

    succeed = Transition(
        [
            full,
            running,
            ActivityStateMachine.open,
            ActivityStateMachine.submitted,
            ActivityStateMachine.rejected,
            ActivityStateMachine.cancelled
        ],
        ActivityStateMachine.succeeded,
        name=_("Succeed"),
        description=_(
            "The event ends and the contributions are counted. Triggered when the event "
            "end time passes."
        ),
    )


@register(Participant)
class ParticipantStateMachine(ContributionStateMachine):
    def is_user(self, user):
        """is the participant"""
        return self.instance.user == user

    def is_activity_owner(self, user):
        """is the participant"""
        return self.instance.activity.owner == user

    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _("The participant withdrew and will no longer attend the activity")
    )
    rejected = State(
        _('rejected'),
        'rejected',
        _("The participant was rejected and will not attend.")
    )
    no_show = State(
        _('no show'),
        'no_show',
        _("The participant didn't attend the event and was marked absent.")
    )
    new = State(
        _('Joined'),
        'new',
        _("The participant signed up for the event.")
    )

    initiate = Transition(
        EmptyState(),
        ContributionStateMachine.new,
        name=_("Join"),
        description=_("Participant is created. User signs up for the activity."),
    )
    withdraw = Transition(
        ContributionStateMachine.new,
        withdrawn,
        name=_('Withdraw'),
        description=_("Participant withdraws from the activity."),
        automatic=False,
        permission=is_user,
    )
    reapply = Transition(
        withdrawn,
        ContributionStateMachine.new,
        name=_('Join again'),
        description=_("Participant signs up for the activity again, after previously withdrawing."),
        automatic=False,
        permission=is_user,
    )
    reject = Transition(
        ContributionStateMachine.new,
        rejected,
        automatic=False,
        name=_('Reject'),
        description=_("Participant is rejected."),
        permission=is_activity_owner
    )

    accept = Transition(
        rejected,
        ContributionStateMachine.new,
        name=_('Accept'),
        description=_("Accept a participant after previously being rejected."),
        automatic=False,
        permission=is_activity_owner
    )

    mark_absent = Transition(
        ContributionStateMachine.succeeded,
        no_show,
        name=_('Mark absent'),
        description=_("The participant didn't show up at the activity and is marked absent."),
        automatic=False,
        permission=is_activity_owner,
    )
    mark_present = Transition(
        no_show,
        ContributionStateMachine.succeeded,
        name=_('Mark present'),
        description=_("The participant showed up, after previously marked absent."),
        automatic=False,
        permission=is_activity_owner,
    )

    succeed = Transition(
        ContributionStateMachine.new,
        ContributionStateMachine.succeeded,
        name=_('Succeed'),
        description=_("The participant successfully took part in the activity."),
    )

    reset = Transition(
        [
            ContributionStateMachine.succeeded,
            ContributionStateMachine.failed,
        ],
        ContributionStateMachine.new,
        name=_('Reset'),
        description=_("The participant is reset to new after being successful or failed."),
    )

    fail = Transition(
        (
            ContributionStateMachine.new,
            ContributionStateMachine.succeeded,
            ContributionStateMachine.failed,
        ),
        ContributionStateMachine.failed,
        name=_('fail'),
        description=_("The contribution failed. It will not be visible in reports."),
    )
