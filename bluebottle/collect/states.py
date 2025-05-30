from django.utils.translation import gettext_lazy as _

from bluebottle.activities.states import (
    ActivityStateMachine, ContributorStateMachine, ContributionStateMachine
)
from bluebottle.collect.models import CollectActivity, CollectContributor, CollectContribution
from bluebottle.fsm.state import register, State, Transition, EmptyState


@register(CollectActivity)
class CollectActivityStateMachine(ActivityStateMachine):
    def has_no_end_date(self):
        """
        Has no end date
        """
        return self.instance.end is None

    def can_succeed(self):
        return len(self.instance.active_contributors) > 0

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
            "The activity will be cancelled because no one has signed up."
        ),
        automatic=True,
    )

    succeed_manually = Transition(
        ActivityStateMachine.open,
        ActivityStateMachine.succeeded,
        automatic=False,
        name=_("succeed"),
        conditions=[has_no_end_date, can_succeed],
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
            "People can contribute again."
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
            'An activity manager can no longer edit the activity '
            'and it will no longer be visible on the platform. '
            'The activity will still be visible in the back office '
            'and will continue to count in the reporting.'
        ),
        automatic=False,
    )


@register(CollectContributor)
class CollectContributorStateMachine(ContributorStateMachine):
    withdrawn = State(
        _('Withdrawn'),
        'withdrawn',
        _('This person has cancelled.')
    )
    rejected = State(
        _('Removed'),
        'rejected',
        _('This person has been removed from the activity.')
    )
    accepted = State(
        _('Participating'),
        'accepted',
        _('This person has been signed up for the activity.')
    )

    def is_user(self, user):
        """is contributor"""
        return (
            self.instance.user == user or
            user in self.instance.activity.owners or
            user.is_staff or
            user.is_superuser
        )

    def is_owner(self, user):
        """is contributor"""
        return (
            user in self.instance.activity.owners or
            user.is_staff or
            user.is_superuser
        )

    def activity_is_open(self):
        """task is open"""
        return self.instance.activity.status == CollectActivityStateMachine.open.value,

    initiate = Transition(
        EmptyState(),
        accepted,
        name=_('initiate'),
        description=_('The contribution was created.')
    )

    succeed = Transition(
        [ContributorStateMachine.new, accepted],
        ContributorStateMachine.succeeded,
        name=_('Succeed'),
        automatic=True,
    )

    re_accept = Transition(
        [
            rejected,
            ContributorStateMachine.failed,
            withdrawn,
        ],
        accepted,
        name=_('Re-Accept'),
        automatic=False,
        permission=is_owner
    )

    accept = Transition(
        ContributorStateMachine.new,
        accepted,
        name=_('Accept'),
        automatic=True
    )

    withdraw = Transition(
        [ContributorStateMachine.succeeded, accepted],
        withdrawn,
        name=_('Withdraw'),
        description=_("Cancel your contribution to this activity."),
        automatic=False,
        permission=is_user,
        hide_from_admin=True,
    )

    reapply = Transition(
        withdrawn,
        accepted,
        name=_('Reapply'),
        description=_("User re-applies after previously cancelling."),
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
        description=_("Remove contributor from the activity."),
        automatic=False,
        permission=is_owner,
    )


@register(CollectContribution)
class CollectContributionStateMachine(ContributionStateMachine):
    pass
