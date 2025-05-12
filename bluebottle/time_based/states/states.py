from django.utils.translation import gettext_lazy as _


from bluebottle.activities.states import (
    ActivityStateMachine, ContributionStateMachine,
)
from bluebottle.fsm.state import (
    register, State, Transition
)
from bluebottle.time_based.models import (
    DateActivity,
    TimeContribution,
    DeadlineActivity,
    PeriodicActivity,
    ScheduleActivity,
    RegisteredDateActivity,
)


class TimeBasedStateMachine(ActivityStateMachine):
    full = State(
        _('Full'),
        'full',
        _('The number of people needed is reached and people can no longer register.')
    )

    lock = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
        ],
        full,
        name=_("Lock"),
        description=_(
            "People can no longer join the event. "
            "Triggered when the attendee limit is reached."
        )
    )
    unlock = Transition(
        full,
        ActivityStateMachine.open,
        name=_("Unlock"),
        description=_(
            "People can now join again. "
            "Triggered when the attendee number drops between the limit."
        )
    )

    reopen = Transition(
        [
            full,
            ActivityStateMachine.succeeded,
            ActivityStateMachine.expired
        ],
        ActivityStateMachine.open,
        name=_("Reopen"),
        passed_label=_('reopened'),
        automatic=True,
        hide_from_admin=True,
        description=_(
            "The number of participants has fallen below the required number or new slots have been added. "
            "People can sign up again for the task."
        )
    )

    reopen_manually = Transition(
        [ActivityStateMachine.expired, ],
        ActivityStateMachine.draft,
        name=_("Reopen"),
        passed_label=_('reopened'),
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
        ],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        description=_(
            'The activity ends and people can no longer register. '
            'Participants will keep their spent hours, '
            'but will no longer be allocated new hours.'),
        automatic=True,
    )

    cancel = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
            full,
        ],
        ActivityStateMachine.cancelled,
        name=_('Cancel'),
        description=_(
            'Cancel if the activity will not be executed. '
            'It will no longer be visible on the platform. '
            'Contributions will not be counted in reporting.'
        ),
        description_front_end=_(
            'The activity will not be executed. Any contributions will be cancelled too.'
        ),
        passed_label=_('cancelled'),
        automatic=False,
        permission=ActivityStateMachine.is_owner,
    )

    expire = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.submitted,
            ActivityStateMachine.succeeded,
            full
        ],
        ActivityStateMachine.expired,
        name=_('Expire'),
        description=_(
            "The activity will be cancelled because no one has signed up for the registration deadline."
        ),
        automatic=True,
    )


@register(DateActivity)
class DateStateMachine(TimeBasedStateMachine):
    reschedule = Transition(
        [ActivityStateMachine.succeeded, ActivityStateMachine.expired],
        ActivityStateMachine.open,
        name=_("Reschedule"),
        permission=ActivityStateMachine.is_owner,
        automatic=True,
        description=_(
            "The activity is reopened because the start date changed."
        )
    )


@register(RegisteredDateActivity)
class RegisteredDateStateMachine(TimeBasedStateMachine):
    pass


class RegistrationActivityStateMachine(TimeBasedStateMachine):
    def can_succeed(self):
        return len(self.instance.active_participants) > 0

    succeed_manually = Transition(
        [ActivityStateMachine.open, TimeBasedStateMachine.full],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        automatic=False,
        description=_("Close this activity and allocate the hours to the participants."),
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


@register(DeadlineActivity)
class DeadlineActivityStateMachine(RegistrationActivityStateMachine):
    pass


@register(ScheduleActivity)
class ScheduleActivityStateMachine(RegistrationActivityStateMachine):
    pass


@register(PeriodicActivity)
class PeriodicActivityStateMachine(RegistrationActivityStateMachine):
    pass


@register(RegisteredDateActivity)
class RegisteredDateActivityStateMachine(TimeBasedStateMachine):

    def has_participants(self):
        return self.instance.participants.count() > 0

    planned = State(
        _('Planned'),
        'planned',
        _('The activity is planned. The activity manager will register participants.')
    )

    succeed = ActivityStateMachine.succeed.extend(
        sources=[planned, ActivityStateMachine.expired],
    )

    register = Transition(
        [
            TimeBasedStateMachine.submitted,
            TimeBasedStateMachine.draft,
            TimeBasedStateMachine.needs_work,
        ],
        planned,
        name=_("Register"),
        description=_('Register your activity, so it will be visible on the platform.'),
        automatic=False,
        passed_label=_("registered"),
        permission=TimeBasedStateMachine.is_owner,
        conditions=[
            TimeBasedStateMachine.is_complete,
            TimeBasedStateMachine.is_valid,
            TimeBasedStateMachine.can_publish,
            has_participants
        ],
    )
    submit = ActivityStateMachine.submit.extend(
        conditions=ActivityStateMachine.submit.conditions + [has_participants],
    )

    publish = None

    approve = ActivityStateMachine.approve.extend(
        description=_('Approve activity, so it will be planned on the platform.'),
        target=planned,
    )

    reopen = TimeBasedStateMachine.reopen.extend(
        target=planned,
        name=_("Reopen"),
        description=_('Reopen activity, so it will be planned on the platform.'),
    )


@register(TimeContribution)
class TimeContributionStateMachine(ContributionStateMachine):
    pass
