from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from bluebottle.fsm.state import State, EmptyState, Transition
from bluebottle.fsm.effects import (
    TransitionEffect,
    RelatedTransitionEffect,
    Effect
)
from bluebottle.follow.effects import (
    FollowActivityEffect, UnFollowActivityEffect
)
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
    "Set time spent on participants"
    post_save = False

    def execute(self):
        if not self.instance.time_spent:
            self.instance.time_spent = self.instance.activity.duration

    def __unicode__(self):
        return _('Set time spent to {} on {}').format(
            self.instance.activity.duration,
            self.instance
        )


class ResetTimeSpent(Effect):
    "Set time spent to 0 if it was not overriden"
    post_save = False

    def execute(self):
        if self.instance.time_spent == self.instance.activity.duration:
            self.instance.time_spent = 0

    def __unicode__(self):
        return _('Reset time spent to 0 on {}').format(
            self.instance
        )


class EventStateMachine(ActivityStateMachine):
    model = Event

    def is_full(self):
        "the event is full"
        return self.instance.capacity == len(self.instance.participants)

    def is_not_full(self):
        "the event is not full"
        return self.instance.capacity > len(self.instance.participants)

    def should_finish(self):
        "the end time has passed"
        return self.instance.end < timezone.now()

    def should_start(self):
        "the start time has passed"
        return self.instance.start < timezone.now()

    def should_open(self):
        "the start time has not passed"
        return self.instance.start > timezone.now()

    def has_participants(self):
        "there are participants"
        return len(self.instance.participants) > 0

    def has_no_participants(self):
        "there are no participants"
        return len(self.instance.participants) == 0

    full = State(_('full'), 'full', _('The activity is full, users can no longer sign up'))
    is_running = State(_('running'), 'running', _('The activity is currently running'))

    approve = Transition(
        ActivityStateMachine.in_review,
        ActivityStateMachine.open,
        name=_('Approve'),
        effects=[
            TransitionEffect(
                'close',
                conditions=[should_finish, has_no_participants]
            ),
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

    start = Transition(
        [ActivityStateMachine.open, full],
        is_running
    )

    succeed = Transition(
        (full, is_running, ActivityStateMachine.open, ActivityStateMachine.closed, ),
        ActivityStateMachine.succeeded,
        effects=[
            NotificationEffect(EventSucceededOwnerMessage),
            RelatedTransitionEffect('participants', 'succeed')
        ]
    )
    close = Transition(
        (
            full,
            is_running,
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
    no_show = State(_('no show'), 'no_show')

    def is_user(self, user):
        return self.instance.user == user

    def is_activity_owner(self, user):
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
        return self.instance.activity.end < timezone.now()

    def event_is_not_finished(self):
        "event is not finished"
        return not self.instance.activity.start < timezone.now()

    def event_will_be_empty(self):
        "event will be empty"
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
            FollowActivityEffect,
        ]
    )
    withdraw = Transition(
        ContributionStateMachine.new,
        withdrawn,
        name=_('Withdraw'),
        automatic=False,
        permission=is_user,
        effects=[
            RelatedTransitionEffect('activity', 'unfill', conditions=[event_will_become_open]),
            UnFollowActivityEffect
        ]
    )
    reapply = Transition(
        withdrawn,
        ContributionStateMachine.new,
        name=_('Join'),
        automatic=False,
        permission=is_user,
        effects=[
            RelatedTransitionEffect('activity', 'fill', conditions=[event_will_become_full]),
            FollowActivityEffect
        ]
    )
    reject = Transition(
        ContributionStateMachine.new,
        rejected,
        automatic=False,
        name=_('Reject'),
        effects=[
            RelatedTransitionEffect('activity', 'unfill'),
            NotificationEffect(ParticipantRejectedMessage),
            UnFollowActivityEffect
        ],
        permission=is_activity_owner
    )
    reaccept = Transition(
        rejected,
        ContributionStateMachine.new,
        name=_('Re-accept'),
        automatic=False,
        effects=[
            RelatedTransitionEffect('activity', 'fill', conditions=[event_will_become_full]),
            FollowActivityEffect
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
                conditions=[event_is_finished, event_will_be_empty]
            ),
            UnFollowActivityEffect
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
                conditions=[event_is_finished]
            ),
            FollowActivityEffect
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
        effects=[ResetTimeSpent, UnFollowActivityEffect]
    )
