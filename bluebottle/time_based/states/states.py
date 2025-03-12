from django.utils.translation import gettext_lazy as _

from bluebottle.activities.states import (
    ActivityStateMachine, ContributionStateMachine,
)
from bluebottle.fsm.state import (
    register, State, Transition, EmptyState, ModelStateMachine
)
from bluebottle.time_based.models import (
    DateActivity,
    TimeContribution,
    SlotParticipant,
    DeadlineActivity,
    PeriodicActivity,
    ScheduleActivity,
)
from bluebottle.time_based.states.slots import DateActivitySlotStateMachine


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
        description=_(
            "The number of participants has fallen below the required number or new slots have been added. "
            "People can sign up again for the task."
        )
    )

    reopen_manually = Transition(
        [ActivityStateMachine.succeeded, ActivityStateMachine.expired],
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

    publish = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
        ],
        ActivityStateMachine.open,
        description=_("Your activity will be open to contributions."),
        automatic=False,
        name=_("Publish"),
        passed_label=_("published"),
        permission=ActivityStateMachine.is_owner,
        conditions=[
            ActivityStateMachine.is_complete,
            ActivityStateMachine.is_valid,
            ActivityStateMachine.initiative_is_approved
        ],
    )

    auto_publish = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
        ],
        ActivityStateMachine.open,
        description=_('Automatically publish activity when initiative is approved'),
        automatic=True,
        name=_('Auto-publish'),
        conditions=[
            ActivityStateMachine.is_complete,
            ActivityStateMachine.is_valid,
        ],
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

    publish = Transition(
        [
            ActivityStateMachine.submitted,
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
        ],
        ActivityStateMachine.open,
        description=_("Your activity will be open to contributions."),
        automatic=False,
        name=_('Publish'),
        passed_label=_('published'),
        permission=ActivityStateMachine.is_owner,
        conditions=[
            ActivityStateMachine.is_complete,
            ActivityStateMachine.is_valid,
            ActivityStateMachine.initiative_is_approved
        ],
    )

    auto_publish = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
        ],
        ActivityStateMachine.open,
        description=_('Automatically publish activity when initiative is approved'),
        automatic=True,
        name=_('Auto-publish'),
        conditions=[
            ActivityStateMachine.is_complete,
            ActivityStateMachine.is_valid,
        ],
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


@register(SlotParticipant)
class SlotParticipantStateMachine(ModelStateMachine):
    registered = State(
        _('registered'),
        'registered',
        _("This person registered.")
    )
    succeeded = State(
        _('succeeded'),
        'succeeded',
        _("The contribution was successful.")
    )
    removed = State(
        _('removed'),
        'removed',
        _('This person no longer takes part.')
    )
    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _('This person has withdrawn. Spent hours are retained.')
    )
    cancelled = State(
        _('cancelled'),
        'cancelled',
        _("The contribution was cancelled. This person's contribution "
          "is removed and the spent hours are reset to zero.")
    )

    def is_user(self, user):
        """is participant"""
        return self.instance.user == user

    def can_accept_participant(self, user):
        """can accept participant"""
        return (
            user in [
                self.instance.activity.owner,
                self.instance.activity.initiative.owner
            ] or
            user.is_staff or
            user in self.instance.activity.initiative.activity_managers.all()
        )

    def slot_is_open(self):
        """task is open"""
        return self.instance.slot_id and self.instance.slot.status in (
            DateActivitySlotStateMachine.open.value,
            DateActivitySlotStateMachine.running.value,
        )

    initiate = Transition(
        EmptyState(),
        registered,
        name=_('Initiate'),
        description=_("User registered to join the slot."),
    )

    accept = Transition(
        [removed, withdrawn, cancelled],
        registered,
        name=_('Accept'),
        passed_label=_('accepted'),
        description=_("Accept the previously rejected person as a participant."),
        description_front_end=_("Do you want to accept this person as a participant?"),
        automatic=False,
        permission=can_accept_participant,
    )

    remove = Transition(
        registered,
        removed,
        name=_('Remove'),
        passed_label=_('removed'),
        description=_("Remove this person as a participant."),
        automatic=False,
        permission=can_accept_participant,
    )

    withdraw = Transition(
        registered,
        withdrawn,
        name=_('Withdraw'),
        passed_label=_('withdrawn'),
        description=_("Cancel the participation."),
        description_front_end=_(
            "You will no longer participate in this time slot. "
            "You can rejoin as long as the activity is open."
        ),
        automatic=False,
        permission=is_user,
        hide_from_admin=True,
    )

    reapply = Transition(
        withdrawn,
        registered,
        name=_('Reapply'),
        passed_label=_('reapplied'),
        description=_("User re-applies after previously withdrawing."),
        description_front_end=_(
            "Do you want to join this time slot again?"
        ),
        automatic=False,
        conditions=[slot_is_open],
        permission=is_user,
    )

    reset = Transition(
        [succeeded, cancelled],
        registered,
        name=_('Reset'),
        passed_label=_('reset'),
        description=_("User is reset to registered."),
        automatic=True,
    )

    succeed = Transition(
        [removed, withdrawn, cancelled, registered],
        succeeded,
        name=_('Succeed'),
        passed_label=_('succeeded'),
        description=_("Succeed the participant, because the slot has finished."),
        automatic=True,
    )


@register(TimeContribution)
class TimeContributionStateMachine(ContributionStateMachine):
    pass
