from django.utils.translation import gettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributorStateMachine
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.fsm.state import register, State, Transition, EmptyState


@register(Deed)
class DeedStateMachine(ActivityStateMachine):
    def has_no_end_date(self):
        return self.instance.end is None

    succeed = Transition(
        [ActivityStateMachine.open, ActivityStateMachine.expired],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        automatic=True,
    )

    expire = Transition(
        [
            ActivityStateMachine.open, ActivityStateMachine.submitted,
            ActivityStateMachine.succeeded
        ],
        ActivityStateMachine.expired,
        name=_('Expire'),
        description=_(
            "The activity will be cancelled because no one has signed up for the registration deadline."
        ),
        automatic=True,
    )

    succeed_manually = Transition(
        ActivityStateMachine.open,
        ActivityStateMachine.succeeded,
        automatic=False,
        name=_("succeed"),
        conditions=[has_no_end_date],
        permission=ActivityStateMachine.is_owner,
        description=_("Succeed the activity.")
    )

    reopen = Transition(
        [
            ActivityStateMachine.expired,
            ActivityStateMachine.succeeded,
        ],
        ActivityStateMachine.open,
        name=_("Reopen"),
        description=_("Reopen the activity.")
    )

    reopen_manually = Transition(
        [ActivityStateMachine.succeeded, ActivityStateMachine.expired],
        ActivityStateMachine.draft,
        name=_("Reopen"),
        permission=ActivityStateMachine.is_owner,
        automatic=False,
        description=_(
            "Manually reopen the activity. "
            "This will unset the end date if the date is in the past. "
            "People can sign up again for the task."
        )
    )

    cancel = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
        ],
        ActivityStateMachine.cancelled,
        name=_('Cancel'),
        permission=ActivityStateMachine.is_owner,
        description=_(
            'Cancel if the activity will not be executed. '
            'The activity manager can no longer edit the activity '
            'and it will no longer be visible on the platform. '
            'The activity will still be visible in the back office '
            'and will continue to count in the reporting.'
        ),
        automatic=False,
        hide_from_admin=True,
    )


@register(DeedParticipant)
class DeedParticipantStateMachine(ContributorStateMachine):
    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _('This person has withdrawn.')
    )
    rejected = State(
        _('Removed'),
        'rejected',
        _('This person has been removed from the activity.')
    )
    accepted = State(
        _('Participating'),
        'accepted',
        _('This person has been signed up for the activity and was accepted automatically.')
    )

    def is_user(self, user):
        """is participant"""
        return self.instance.user == user

    def is_owner(self, user):
        """is participant"""
        return (
            self.instance.activity.owner == user or
            self.instance.activity.initiative.owner == user or
            self.instance.activity.initiative.activity_manager == user or
            user.is_staff
        )

    def activity_is_open(self):
        """task is open"""
        return self.instance.activity.status == DeedStateMachine.open.value,

    initiate = Transition(
        EmptyState(),
        accepted,
        name=_('initiate'),
        description=_('The contribution was created.')
    )

    succeed = Transition(
        accepted,
        ContributorStateMachine.succeeded,
        name=_('Succeed'),
        automatic=True,
    )

    re_accept = Transition(
        ContributorStateMachine.succeeded,
        accepted,
        name=_('Re-accept'),
        automatic=True,
    )

    withdraw = Transition(
        [ContributorStateMachine.succeeded, accepted],
        withdrawn,
        name=_('Withdraw'),
        description=_("Stop your participation in the activity."),
        automatic=False,
        permission=is_user,
        hide_from_admin=True,
    )

    reapply = Transition(
        withdrawn,
        accepted,
        name=_('Reapply'),
        description=_("User re-applies after previously withdrawing."),
        automatic=False,
        conditions=[activity_is_open],
        permission=is_user,
    )

    remove = Transition(
        [
            accepted,
            ContributorStateMachine.succeeded
        ],
        rejected,
        name=_('Remove'),
        description=_("Remove participant from the activity."),
        automatic=False,
        permission=is_owner,
    )

    accept = Transition(
        rejected,
        accepted,
        name=_('Re-Accept'),
        description=_("User is re-accepted after previously withdrawing."),
        automatic=False,
        permission=is_owner,
    )
