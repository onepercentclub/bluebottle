from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import (
    register, State, Transition, EmptyState, ModelStateMachine
)
from bluebottle.time_based.models import (
    PeriodicSlot,
    ScheduleSlot,
    TeamScheduleSlot,
    DateActivitySlot
)


class SlotStateMachine(ModelStateMachine):
    new = State(_("Unscheduled"), "new", _("The slot is not scheduled yet."))
    scheduled = State(
        _("Scheduled"), "scheduled", _("The slot is scheduled for a future date.")
    )

    running = State(
        _('Running'),
        'running',
        _('The slot running.')
    )

    finished = State(
        _('Finished'),
        'finished',
        _('The slot is finished')
    )

    cancelled = State(
        _('Cancelled'),
        'cancelled',
        _('The slot is cancelled')
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
        new,
        name=_('Initiate'),
        description=_(
            'The slot was created.'
        ),
        automatic=True
    )

    schedule = Transition(
        [new, finished, running, scheduled],
        scheduled,
        name=_("Schedule"),
        description=_("The slot now has a date and location."),
        automatic=True,
    )

    unschedule = Transition(
        [scheduled, running, finished],
        new,
        name=_("Reset"),
        description=_("The slot no longer has a date and location."),
        automatic=True,
    )

    start = Transition(
        [new, scheduled],
        running,
        name=_('Start'),
        description=_(
            'The slot has started.'
        ),
        automatic=True
    )

    finish = Transition(
        [new, running, scheduled],
        finished,
        name=_("Finish"),
        description=_("The slot has finished."),
        automatic=True,
    )

    cancel = Transition(
        [new, running, scheduled],
        cancelled,
        permission=is_activity_owner,
        automatic=False,
        name=_("Cancel"),
        description=_("The slot was cancelled."),
    )

    auto_cancel = Transition(
        [new, running, scheduled],
        cancelled,
        automatic=True,
        name=_("Auto cancel"),
        description=_("The slot was cancelled because a parent object was cancelled"),
    )

    restore = Transition(
        cancelled,
        new,
        permission=is_activity_owner,
        automatic=False,
        name=_("Restore"),
        description=_("The slot was restored."),
    )


@register(PeriodicSlot)
class PeriodicSlotStateMachine(SlotStateMachine):
    pass


@register(ScheduleSlot)
class ScheduleSlotStateMachine(SlotStateMachine):
    pass


@register(TeamScheduleSlot)
class TeamScheduleSlotStateMachine(SlotStateMachine):
    pass


@register(DateActivitySlot)
class DateActivitySlotStateMachine(ModelStateMachine):

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

    restore = Transition(
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
