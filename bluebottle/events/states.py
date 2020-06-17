from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine
from bluebottle.events.effects import SetTimeSpent, ResetTimeSpent
from bluebottle.events.messages import (
    EventSucceededOwnerMessage,
    EventClosedOwnerMessage,
    ParticipantRejectedMessage,
    ParticipantApplicationMessage,
    ParticipantApplicationManagerMessage,
)
from bluebottle.events.models import Event, Participant
from bluebottle.follow.effects import (
    FollowActivityEffect, UnFollowActivityEffect
)
from bluebottle.fsm.effects import (
    TransitionEffect,
    RelatedTransitionEffect
)
from bluebottle.fsm.state import State, EmptyState, Transition
from bluebottle.notifications.effects import NotificationEffect


class EventStateMachine(ActivityStateMachine):
    model = Event
    submitted = State(
        _('submitted'),
        'submitted',
        _('The activity is ready to go online once the initiative has been approved.')
    )

    def is_full(self):
        "the event is full"
        return self.instance.capacity == len(self.instance.participants)

    def is_not_full(self):
        "the event is not full"
        return self.instance.capacity > len(self.instance.participants)

    def should_finish(self):
        "the end time has passed"
        return self.instance.current_end and self.instance.current_end < timezone.now()

    def should_start(self):
        "the start time has passed"
        return self.instance.start and self.instance.start < timezone.now()

    def should_open(self):
        "the start time has not passed"
        return self.instance.start and self.instance.start > timezone.now()

    def has_participants(self):
        "there are participants"
        return len(self.instance.participants) > 0

    def has_no_participants(self):
        "there are no participants"
        return len(self.instance.participants) == 0

    full = State(_('full'), 'full', _('The activity is full, users can no longer sign up'))
    running = State(_('running'), 'running', _('The activity is currently running'))

    approve = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.submitted,
            ActivityStateMachine.rejected,
            ActivityStateMachine.needs_work,
        ],
        ActivityStateMachine.open,
        name=_('Approve'),
        description=_("Approve the event. Users can start signing up to it."),
        effects=[
            RelatedTransitionEffect('organizer', 'succeed'),
            TransitionEffect(
                'close',
                conditions=[should_finish, has_no_participants]
            ),
        ]
    )

    lock = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded
        ],
        full,
        name=_("Lock"),
        description=_("Set the event to full because capacity is reached.")
    )

    reopen = Transition(
        full,
        ActivityStateMachine.open,
        name=_("Reopen"),
        description=_("Set the event to open, because there are spots available again.")
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

    expire = Transition(
        ActivityStateMachine.open,
        ActivityStateMachine.closed,
        name=_("Expire"),
        description=_("Event expired. No one signed-up before the start of the event.")
    )

    succeed = Transition(
        [
            full,
            running,
            ActivityStateMachine.open,
            ActivityStateMachine.closed
        ],
        ActivityStateMachine.succeeded,
        name=_("Succeed"),
        description=_("The event was successfully completed."),
        effects=[
            NotificationEffect(EventSucceededOwnerMessage),
            RelatedTransitionEffect('participants', 'succeed')
        ]
    )

    close = Transition(
        (
            ActivityStateMachine.draft,
            full,
            running,
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
        ),
        ActivityStateMachine.closed,
        name=_("Close"),
        description=_("Close the event. It will no longer be editable by the organiser."),
        effects=[
            NotificationEffect(EventClosedOwnerMessage),
            RelatedTransitionEffect('participants', 'fail')
        ]
    )

    restore = Transition(
        [
            ActivityStateMachine.rejected,
            ActivityStateMachine.closed
        ],
        ActivityStateMachine.open,
        name=_("Restore"),
        description=_("Reopen the event. Users are able to sign up for it again."),
        effects=[
            RelatedTransitionEffect('participants', 'reset'),
            # Need to add organizer,reset() But probably should differentiate between
            # `restore` a closed event and `reschedule` a succeeded one
            # RelatedTransitionEffect('organizer', 'reset')
        ]
    )


class ParticipantStateMachine(ContributionStateMachine):
    model = Participant

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

    def is_user(self, user):
        """is the participant"""
        return self.instance.user == user

    def is_activity_owner(self, user):
        """is the activity manager or a staff member"""
        return user.is_staff or self.instance.activity.owner == user

    def event_will_become_full(self):
        "event will be full"
        activity = self.instance.activity
        return activity.capacity == len(activity.participants) + 1

    def event_will_become_open(self):
        "event will not be full"
        activity = self.instance.activity
        return activity.capacity == len(activity.participants)

    def event_is_finished(self):
        "event is finished"
        return self.instance.activity.current_end < timezone.now()

    def event_is_not_finished(self):
        "event is not finished"
        return not self.instance.activity.start < timezone.now()

    def event_will_be_empty(self):
        "event will be empty"
        return len(self.instance.activity.participants) == 1

    initiate = Transition(
        EmptyState(),
        ContributionStateMachine.new,
        name=_("Join"),
        description=_("Participant is created. User signs up for the activity."),
        effects=[
            TransitionEffect(
                'succeed',
                conditions=[event_is_finished]
            ),
            RelatedTransitionEffect(
                'activity',
                'fill',
                conditions=[event_will_become_full]
            ),
            RelatedTransitionEffect(
                'activity',
                'succeed',
                conditions=[event_is_finished]
            ),
            NotificationEffect(ParticipantApplicationManagerMessage),
            NotificationEffect(ParticipantApplicationMessage),
            FollowActivityEffect,
        ]
    )
    withdraw = Transition(
        ContributionStateMachine.new,
        withdrawn,
        name=_('Withdraw'),
        description=_("Participant withdraws from the activity."),
        automatic=False,
        permission=is_user,
        effects=[
            RelatedTransitionEffect('activity', 'reopen', conditions=[event_will_become_open]),
            UnFollowActivityEffect
        ]
    )
    reapply = Transition(
        withdrawn,
        ContributionStateMachine.new,
        name=_('Join again'),
        description=_("Participant signs up for the activity again, after previously withdrawing."),
        automatic=False,
        permission=is_user,
        effects=[
            TransitionEffect('succeed', conditions=[event_is_finished]),
            RelatedTransitionEffect('activity', 'lock', conditions=[event_will_become_full]),
            FollowActivityEffect
        ]
    )
    reject = Transition(
        ContributionStateMachine.new,
        rejected,
        automatic=False,
        name=_('Reject'),
        description=_("Participant is rejected."),
        effects=[
            RelatedTransitionEffect('activity', 'reopen'),
            NotificationEffect(ParticipantRejectedMessage),
            UnFollowActivityEffect
        ],
        permission=is_activity_owner
    )
    accept = Transition(
        rejected,
        ContributionStateMachine.new,
        name=_('Accept'),
        description=_("Accept a participant after previously being rejected."),
        automatic=False,
        effects=[
            TransitionEffect('succeed', conditions=[event_is_finished]),
            RelatedTransitionEffect('activity', 'lock', conditions=[event_will_become_full]),
            FollowActivityEffect
        ],
        permission=is_activity_owner
    )

    mark_absent = Transition(
        ContributionStateMachine.succeeded,
        no_show,
        name=_('Mark absent'),
        description=_("The participant didn't show up at the activity and is marked absent."),
        automatic=False,
        permission=is_activity_owner,
        effects=[
            ResetTimeSpent,
            RelatedTransitionEffect(
                'activity', 'close',
                conditions=[event_is_finished, event_will_be_empty]
            ),
            UnFollowActivityEffect
        ]
    )
    mark_present = Transition(
        no_show,
        ContributionStateMachine.succeeded,
        name=_('Mark present'),
        description=_("The participant showed up, after previously marked absent."),
        automatic=False,
        permission=is_activity_owner,
        effects=[
            SetTimeSpent,
            RelatedTransitionEffect(
                'activity', 'succeed',
                conditions=[event_is_finished]
            ),
            FollowActivityEffect
        ]
    )

    succeed = Transition(
        ContributionStateMachine.new,
        ContributionStateMachine.succeeded,
        name=_('Succeed'),
        description=_("The participant successfully took part in the activity."),
        effects=[
            SetTimeSpent,
            RelatedTransitionEffect(
                'activity', 'succeed',
                conditions=[event_is_finished])
        ]
    )

    reset = Transition(
        ContributionStateMachine.succeeded,
        ContributionStateMachine.new,
        name=_('Reset'),
        description=_("The participant is reset to new after being successful."),
        effects=[ResetTimeSpent]
    )
