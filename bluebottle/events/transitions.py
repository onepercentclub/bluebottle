from django.forms.models import model_to_dict
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from djchoices.choices import ChoiceItem

from bluebottle.fsm import transition
from bluebottle.activities.transitions import ActivityTransitions, ContributionTransitions
from bluebottle.events.messages import EventDoneOwnerMessage, EventClosedOwnerMessage


class EventTransitions(ActivityTransitions):
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

    def is_complete(self):
        from bluebottle.events.serializers import EventSubmitSerializer
        serializer = EventSubmitSerializer(
            data=model_to_dict(self.instance)
        )
        if not serializer.is_valid():
            return _('Please make sure all required fields are filled in')

    def initiative_is_approved(self):
        if not self.instance.initiative.status == 'approved':
            return _('Please make sure the initiative is approved')

    @transition(
        source=ActivityTransitions.values.draft,
        target=ActivityTransitions.values.open,
        conditions=[is_complete, initiative_is_approved],
        serializer='bluebottle.events.serializers.EventSubmitSerializer',
    )
    def open(self):
        pass

    @transition(
        source=ActivityTransitions.values.open,
        target=ActivityTransitions.values.full,
        conditions=[can_open]
    )
    def full(self):
        pass

    @transition(
        source=ActivityTransitions.values.full,
        target=ActivityTransitions.values.open,
        conditions=[can_open]
    )
    def reopen(self):
        pass

    @transition(
        source=ActivityTransitions.values.closed,
        target=ActivityTransitions.values.draft,
    )
    def redraft(self, **kwargs):
        pass

    @transition(
        source=[ActivityTransitions.values.full, ActivityTransitions.values.open],
        target=ActivityTransitions.values.running,
        conditions=[can_start]
    )
    def start(self, **kwargs):
        pass

    @transition(
        source=ActivityTransitions.values.running,
        target=ActivityTransitions.values.done,
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
        target=ActivityTransitions.values.closed,
        messages=[EventClosedOwnerMessage]
    )
    def close(self):
        pass

    @transition(
        source=ActivityTransitions.values.closed,
        target=ActivityTransitions.values.open,
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
        permissions=[is_user],
        follow=False
    )
    def withdraw(self):
        pass

    @transition(
        source=values.withdrawn,
        target=values.new,
        conditions=[event_is_open_or_full],
        follow=True
    )
    def reapply(self):
        pass

    @transition(
        source=[values.new],
        target=values.rejected,
        permissions=[ContributionTransitions.is_activity_manager],
        follow=False
    )
    def reject(self):
        pass

    @transition(
        source=[values.new, values.no_show, values.rejected, values.withdrawn],
        target=values.success,
        conditions=[event_is_done],
        follow=True
    )
    def success(self):
        self.instance.time_spent = self.instance.activity.duration

    @transition(
        source=values.success,
        target=values.no_show,
        permissions=[ContributionTransitions.is_activity_manager],
        follow=False
    )
    def no_show(self):
        self.instance.time_spent = 0

    @transition(
        source='*',
        target=values.closed,
        follow=False
    )
    def close(self):
        self.instance.time_spent = 0
