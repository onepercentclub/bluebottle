from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from djchoices.choices import ChoiceItem

from bluebottle.fsm import transition
from bluebottle.follow.models import follow, unfollow
from bluebottle.activities.transitions import ActivityTransitions, ContributionTransitions
from bluebottle.events.messages import EventDoneOwnerMessage, EventClosedOwnerMessage


class EventTransitions(ActivityTransitions):
    serializer = 'bluebottle.events.serializers.EventSubmitSerializer'

    class values(ActivityTransitions.values):
        full = ChoiceItem('full', _('full'))
        running = ChoiceItem('running', _('running'))

    def can_start(self):
        if not self.instance.start_time:
            return _('Start date has not been set')
        if self.instance.start_time > now():
            return _('The start date has not passed')

    def can_open(self):
        if not self.instance.start_time:
            return _('Start date has not been set')
        if self.instance.start_time < now():
            return _('The start date has passed')

    def can_end(self):
        if not self.instance.end_time:
            return _('End date has not been set')
        if not self.instance.end_time < now():
            return _('The end date has not passed')

    @transition(
        source=values.open,
        target=values.full,
        conditions=[can_open]
    )
    def full(self):
        pass

    @transition(
        source=values.full,
        target=values.open,
        conditions=[can_open]
    )
    def reopen(self):
        pass

    @transition(
        source=values.closed,
        target=values.draft,
    )
    def redraft(self, **kwargs):
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
        target=values.done,
        conditions=[can_end],
        messages=[EventDoneOwnerMessage]
    )
    def done(self):
        for member in self.instance.participants:
            member.activity = self.instance
            member.transitions.success()
            member.save()

    @transition(
        source='*',
        target=values.closed,
        messages=[EventClosedOwnerMessage]
    )
    def close(self):
        pass

    @transition(
        source=values.closed,
        target=values.open,
        conditions=[can_open]
    )
    def extend(self):
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

    def event_is_done(self):
        if not self.instance.activity.status == EventTransitions.values.done:
            return _('The event is not done')

    def is_user(self, user):
        return self.instance.user == user

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
        permissions=[ContributionTransitions.is_activity_manager]
    )
    def reject(self):
        unfollow(self.instance.user, self.instance.activity)

    @transition(
        source=[values.new, values.no_show, values.rejected, values.withdrawn],
        target=values.success,
        conditions=[event_is_done]
    )
    def success(self):
        follow(self.instance.user, self.instance.activity)
        self.instance.time_spent = self.instance.activity.duration

    @transition(
        source=values.success,
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
