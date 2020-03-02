from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from bluebottle.fsm.state import State, EmptyState, Transition
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect, Effect
from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine

from bluebottle.events.models import Event, Participant
from bluebottle.events.messages import (
    EventSucceededOwnerMessage,
    EventClosedOwnerMessage,
    ParticipantRejectedMessage,
    ParticipantApplicationMessage,
    ParticipantApplicationManagerMessage,
)

from bluebottle.notifications.effects import NotificationEffect


class SetTimeSpent(Effect):
    post_save = False

    def execute(self):
        if not self.instance.time_spent:
            self.instance.time_spent = self.instance.activity.duration


class ResetTimeSpent(Effect):
    post_save = False

    def execute(self):
        if self.instance.time_spent == self.instance.activity.duration:
            self.instance.time_spent = 0


class EventStateMachine(ActivityStateMachine):
    model = Event

    def is_full(self):
        return self.instance.capacity == len(self.instance.participants)

    def is_not_full(self):
        return self.instance.capacity > len(self.instance.participants)

    def should_finish(self):
        return self.instance.start < timezone.now()

    def should_open(self):
        return self.instance.start > timezone.now()

    def has_participants(self):
        return len(self.instance.participants) > 0

    def has_no_participants(self):
        return len(self.instance.participants) == 0

    full = State(_('full'), 'full')
    is_running = State(_('running'), 'running')

    approve = Transition(
        ActivityStateMachine.in_review,
        ActivityStateMachine.open,
        name=_('Approve'),
        effects=[
            TransitionEffect('close', conditions=[should_finish, has_no_participants]),
        ]
    )

    fill = Transition(
        (ActivityStateMachine.open, ActivityStateMachine.succeeded, ),
        full
    )
    unfill = Transition(
        full,
        ActivityStateMachine.open
    )

    succeed = Transition(
        (full, ActivityStateMachine.open, ActivityStateMachine.closed, ),
        ActivityStateMachine.succeeded,
        effects=[
            NotificationEffect(EventSucceededOwnerMessage),
            RelatedTransitionEffect('participants', 'succeed')
        ]
    )
    close = Transition(
        (
            full,
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
            ActivityStateMachine.in_review,
        ),
        ActivityStateMachine.closed,
        effects=[NotificationEffect(EventClosedOwnerMessage)]
    )
    reopen = Transition(
        (ActivityStateMachine.succeeded, ActivityStateMachine.closed, ),
        ActivityStateMachine.open,
        effects=[RelatedTransitionEffect('participants', 'reset')]
    )


class ParticipantStateMachine(ContributionStateMachine):
    model = Participant

    withdrawn = State(_('withdrawn'), 'withdrawn')
    rejected = State(_('rejected'), 'rejected')
    no_show = State(_('no_show'), 'no_show')

    def is_user(self, user):
        return self.instance.user == user

    def is_activity_owner(self, user):
        return user.is_staff or self.instance.activity.owner == user

    def event_will_become_full(self):
        activity = self.instance.activity
        return activity.capacity == len(activity.participants) + 1

    def event_will_become_open(self):
        activity = self.instance.activity
        return activity.capacity == len(activity.participants)

    def event_is_finished(self):
        return self.instance.activity.start < timezone.now()

    def event_will_be_empty(self):
        return len(self.instance.activity.participants) == 1

    initiate = Transition(
        EmptyState(),
        ContributionStateMachine.new,
        effects=[
            TransitionEffect('succeed', conditions=[event_is_finished]),
            RelatedTransitionEffect('activity', 'fill', conditions=[event_will_become_full]),
            RelatedTransitionEffect(
                'activity',
                'succeed',
                conditions=[event_is_finished]
            ),
            NotificationEffect(ParticipantApplicationManagerMessage),
            NotificationEffect(ParticipantApplicationMessage),
        ]
    )
    withdraw = Transition(
        ContributionStateMachine.new,
        withdrawn,
        name=_('Withdraw'),
        automatic=False,
        permission=is_user,
        effects=[RelatedTransitionEffect('activity', 'unfill', conditions=[event_will_become_open])]
    )
    join = Transition(
        withdrawn,
        ContributionStateMachine.new,
        name=_('Join'),
        automatic=False,
        permission=is_user,
        effects=[RelatedTransitionEffect('activity', 'fill', conditions=[event_will_become_full])]
    )
    reject = Transition(
        ContributionStateMachine.new,
        rejected,
        automatic=False,
        name=_('Reject'),
        effects=[
            RelatedTransitionEffect('activity', 'unfill'),
            NotificationEffect(ParticipantRejectedMessage),
        ],
        permission=is_activity_owner
    )
    reaccept = Transition(
        rejected,
        ContributionStateMachine.new,
        name=_('Re-accept'),
        automatic=False,
        effects=[
            RelatedTransitionEffect('activity', 'fill', conditions=[event_will_become_full])
        ],
        permission=is_activity_owner
    )

    mark_absent = Transition(
        ContributionStateMachine.succeeded,
        no_show,
        name=_('Mark absent'),
        automatic=False,
        permission=is_activity_owner,
        effects=[
            ResetTimeSpent,
            RelatedTransitionEffect(
                'activity', 'close',
                conditions=[event_is_finished, event_will_be_empty])
        ]
    )
    mark_present = Transition(
        no_show,
        ContributionStateMachine.succeeded,
        name=_('Mark present'),
        automatic=False,
        permission=is_activity_owner,
        effects=[
            SetTimeSpent,
            RelatedTransitionEffect(
                'activity', 'succeed',
                conditions=[event_is_finished])
        ]
    )

    succeed = Transition(
        ContributionStateMachine.new,
        ContributionStateMachine.succeeded,
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
        effects=[ResetTimeSpent]
    )
