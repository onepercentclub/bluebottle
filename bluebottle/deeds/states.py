from django.utils.translation import gettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributorStateMachine
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.fsm.state import register, State, Transition, EmptyState


@register(Deed)
class DeedStateMachine(ActivityStateMachine):
    def has_no_end_date(self):
        """
        Has no end date
        """
        return self.instance.end is None

    def can_succeed(self):
        return len(self.instance.participants) > 0

    succeed = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.expired
        ],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        automatic=True,
    )

    expire = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.submitted,
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
        name=_("Succeed"),
        passed_label=_('succeeded'),
        conditions=[has_no_end_date, can_succeed],
        permission=ActivityStateMachine.is_owner,
        description=_("The activity ends and people can no longer register. ")
    )

    reopen = Transition(
        [
            ActivityStateMachine.expired,
            ActivityStateMachine.succeeded,
        ],
        ActivityStateMachine.open,
        name=_("Reopen"),
        description=_("Reopen the activity."),
    )

    reopen_manually = Transition(
        [
            ActivityStateMachine.succeeded,
            ActivityStateMachine.expired
        ],
        ActivityStateMachine.draft,
        name=_("Reopen"),
        passed_label=_('reopened'),
        permission=ActivityStateMachine.is_owner,
        automatic=False,
        description=_(
            "The activity will be set to the status ‘Needs work’. "
            "Then you can make changes to the activity and submit it again."
        ),
    )

    cancel = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
        ],
        ActivityStateMachine.cancelled,
        name=_('Cancel'),
        passed_label=_('cancelled'),
        permission=ActivityStateMachine.is_owner,
        description=_(
            'Cancel if the activity will not be executed. '
            'An activity manager can no longer edit the activity '
            'and it will no longer be visible on the platform. '
            'The activity will still be visible in the back office '
            'and will continue to count in the reporting.'
        ),
        description_front_end=_(
            'The activity ends and people can no longer register.'
        ),
        automatic=False,
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
            user in self.instance.activity.owners or
            user.is_staff or
            user.is_superuser
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
        name=_('Reaccept'),
        description=_("Put a participant back as participating after it was successful."),
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
        description=_("Reapply after previously withdrawing."),
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
        [rejected, withdrawn],
        accepted,
        name=_('Reaccept'),
        description=_("Reaccept user after previously withdrawing or rejecting."),
        automatic=False,
        permission=is_owner,
    )
