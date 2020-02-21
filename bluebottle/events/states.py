from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from bluebottle.fsm.state import State
from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine

from bluebottle.events.messages import (
    EventSucceededOwnerMessage,
    EventClosedOwnerMessage,
    ParticipantRejectedMessage,
)


class EventStateMachine(ActivityStateMachine):
    full = State(_('full'), 'full')
    is_running = State(_('running'), 'running')

    def is_full(self):
        return len(self.instance.participants) >= self.instance.capacity

    def is_not_full(self):
        return not self.is_full()

    def has_finished(self):
        return self.instance.end < timezone.now()

    def has_not_finished(self):
        return not self.has_finished()

    def has_participants(self):
        return len(self.instance.participants)

    def has_no_participants(self):
        return not self.has_participants()

    fill = ActivityStateMachine.open.to(
        full, conditions=[is_full]
    )
    unfill = full.to(
        ActivityStateMachine.open, conditions=[is_not_full]
    )

    succeed = (full | ActivityStateMachine.open | ActivityStateMachine.closed).to(
        ActivityStateMachine.succeeded,
        conditions=[has_finished, has_participants],
        messages=[EventSucceededOwnerMessage]
    )
    close = (full | ActivityStateMachine.open | ActivityStateMachine.closed).to(
        ActivityStateMachine.succeeded, conditions=[has_finished, has_no_participants]
    )

    reopen = (ActivityStateMachine.succeeded | ActivityStateMachine.closed).to(
        ActivityStateMachine.open,
        conditions=[has_not_finished]
    )


class ParticipantStateMachine(ContributionStateMachine):
    withdrawn = State(_('withdrawn'), 'withdrawn')
    rejected = State(_('rejected'), 'rejected')
    no_show = State(_('no_show'), 'no_show')

    def event_is_open(self):
        return self.instance.activity.status in ('open', 'full')

    def is_user(self, user):
        return self.instance.user == user

    def is_activity_owner(self, user):
        return user.is_staff or self.instance.activity.owner == user

    withdraw = ContributionStateMachine.new.to(withdrawn, automatic=False, permission=is_user)
    unwithdraw = withdrawn.to(ContributionStateMachine.new, automatic=False, permission=is_user)
    reject = ContributionStateMachine.new.to(
        rejected,
        automatic=False,
        messages=[ParticipantRejectedMessage],
        permission=is_activity_owner
    )
    unreject = rejected.to(
        ContributionStateMachine.new,
        automatic=False,
        messages=[ParticipantRejectedMessage],
        permission=is_activity_owner
    )

    mark_absent = ContributionStateMachine.succeeded.to(
        no_show, automatic=False, permission=is_activity_owner
    )
    mark_present = no_show.to(
        ContributionStateMachine.succeeded, automatic=False, permission=is_activity_owner
    )

    succeed = ContributionStateMachine.new.to(
        ContributionStateMachine.succeeded,
        conditions=[ContributionStateMachine.activity_is_succeeded]
    )

    reset = ContributionStateMachine.succeeded.to(
        ContributionStateMachine.new,
        conditions=[event_is_open]
    )
