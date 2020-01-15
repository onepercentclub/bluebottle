from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from djchoices.choices import ChoiceItem

from bluebottle.initiatives.transitions import ReviewTransitions

from bluebottle.activities.transitions import ActivityTransitions, ContributionTransitions
from bluebottle.events.messages import (
    EventSucceededOwnerMessage,
    EventClosedOwnerMessage,
    ParticipantApplicationMessage,
    ParticipantRejectedMessage,

)

from bluebottle.follow.models import follow, unfollow
from bluebottle.fsm import transition


class EventTransitions(ActivityTransitions):

    class values(ActivityTransitions.values):
        full = ChoiceItem('full', _('full'))
        running = ChoiceItem('running', _('running'))

    def can_start(self):
        if not self.instance.start:
            return _('Start date has not been set')
        if self.instance.start > now():
            return _('The start date has not passed')

    def can_open(self):
        if self.instance.review_transitions.is_complete():
            return _('The event is not complete')
        if self.instance.review_status != ReviewTransitions.values.approved:
            return _('The event is not approved')
        if not self.instance.start:
            return _('Start date has not been set')
        if self.instance.start < now():
            return _('The start date has passed')

    def can_end(self):
        if not self.instance.duration:
            return _('Duration has not been set')
        if not self.instance.end < now():
            return _('The end date has not passed')

    @transition(
        source=values.open,
        target=values.full,
    )
    def full(self):
        pass

    @transition(
        source=[values.full, values.closed],
        target=values.open,
        permissions=[ActivityTransitions.can_approve]
    )
    def reopen(self):
        pass

    @transition(
        source=[values.full, values.open],
        target=values.running,
        conditions=[can_start]
    )
    def start(self, **kwargs):
        pass

    @transition(
        source=values.running,
        target=values.succeeded,
        conditions=[can_end],
        messages=[EventSucceededOwnerMessage]
    )
    def succeed(self):
        for member in self.instance.participants:
            member.activity = self.instance
            member.transitions.succeed()
            member.save()

    @transition(
        field='status',
        source=[values.closed],
        target=values.succeeded,
        permissions=[ActivityTransitions.is_system],
        messages=[EventSucceededOwnerMessage]
    )
    def reopen_and_succeed(self, **kwargs):
        states = [
            ParticipantTransitions.values.new,
            ParticipantTransitions.values.closed,
            ParticipantTransitions.values.succeeded
        ]
        for member in self.instance.contributions.filter(status__in=states):
            member.activity = self.instance
            member.transitions.succeed()
            member.save()

    @transition(
        source='*',
        target=values.closed,
        messages=[EventClosedOwnerMessage],
        permissions=[ActivityTransitions.can_approve]
    )
    def close(self):
        for participant in self.instance.participants:
            participant.transitions.close()
            participant.save()

    @transition(
        source=values.closed,
        target=values.open,
        conditions=[can_open]
    )
    def extend(self):
        pass

    @transition(
        source=values.in_review,
        target=values.open,
        permissions=[ActivityTransitions.can_approve]
    )
    def reviewed(self):
        pass


class ParticipantTransitions(ContributionTransitions):
    class values(ContributionTransitions.values):
        withdrawn = ChoiceItem('withdrawn', _('withdrawn'))
        rejected = ChoiceItem('rejected', _('rejected'))
        no_show = ChoiceItem('no_show', _('no_show'))
        closed = ChoiceItem('closed', _('closed'))

    def event_is_open(self):
        if not self.instance.activity.status == EventTransitions.values.open:
            return _('The event is not open')

    def event_is_open_or_full(self):
        if self.instance.activity.status not in (EventTransitions.values.open, EventTransitions.values.full):
            return _('The event is not open or full')

    def event_is_successful(self):
        if not self.instance.activity.status == EventTransitions.values.succeeded:
            return _('The event is not successful')

    def is_user(self, user):
        return self.instance.user == user

    @transition(
        source=[ContributionTransitions.values.new],
        target=ContributionTransitions.values.new,
        messages=[ParticipantApplicationMessage]
    )
    def initiate(self):
        pass

    @transition(
        source=values.new,
        target=values.withdrawn,
        conditions=[event_is_open_or_full],
        permissions=[is_user]
    )
    def withdraw(self):
        unfollow(self.instance.user, self.instance.activity)

    @transition(
        source=values.withdrawn,
        target=values.new,
        conditions=[event_is_open_or_full]
    )
    def reapply(self):
        follow(self.instance.user, self.instance.activity)

    @transition(
        source=[values.new],
        target=values.rejected,
        permissions=[ContributionTransitions.is_activity_manager],
        messages=[ParticipantRejectedMessage]
    )
    def reject(self):
        unfollow(self.instance.user, self.instance.activity)

    @transition(
        source=[values.rejected],
        target=values.new,
        permissions=[ContributionTransitions.is_activity_manager]
    )
    def unreject(self):
        follow(self.instance.user, self.instance.activity)

    @transition(
        source='*',
        target=values.succeeded,
        conditions=[event_is_successful]
    )
    def succeed(self):
        follow(self.instance.user, self.instance.activity)
        self.instance.time_spent = self.instance.activity.duration

    @transition(
        source=values.succeeded,
        target=values.no_show,
        permissions=[ContributionTransitions.is_activity_manager]
    )
    def no_show(self):
        unfollow(self.instance.user, self.instance.activity)
        self.instance.time_spent = 0

    @transition(
        source='*',
        target=values.closed,
    )
    def close(self):
        self.instance.time_spent = 0
