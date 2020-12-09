from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.models import Organizer, OrganizerContribution
from bluebottle.fsm.state import ModelStateMachine, State, EmptyState, AllStates, Transition, register


class ActivityStateMachine(ModelStateMachine):
    draft = State(
        _('draft'),
        'draft',
        _('The activity has been created, but not yet completed. The activity manager is still editing the activity.')
    )
    submitted = State(
        _('submitted'),
        'submitted',
        _('The activity is ready to go online once the initiative has been approved.')
    )
    needs_work = State(
        _('needs work'),
        'needs_work',
        _('The activity has been submitted but needs adjustments in order to be approved.')
    )
    rejected = State(
        _('rejected'),
        'rejected',
        _(
            'The activity does not fit the programme or does not comply with the rules. '
            'The activity does not appear on the platform, but counts in the report. '
            'The activity cannot be edited by the activity manager.'
        )
    )
    deleted = State(
        _('deleted'),
        'deleted',
        _(
            'The activity has been removed. The activity does not appear on '
            'the platform and does not count in the report. '
            'The activity cannot be edited by the activity manager.'
        )
    )
    cancelled = State(
        _('cancelled'),
        'cancelled',
        _(
            'The activity is not executed. The activity does not appear on the platform, '
            'but counts in the report. The activity cannot be edited by the activity manager.'
        )
    )

    expired = State(
        _('expired'),
        'expired',
        _(
            'The activity has ended, but did have any contributions . The activity does not appear on the platform, '
            'but counts in the report. The activity cannot be edited by the activity manager.'
        )
    )
    open = State(
        _('open'),
        'open',
        _('The activity is accepting new contributions.')
    )
    succeeded = State(
        _('succeeded'),
        'succeeded',
        _('The activity has ended successfully.')
    )

    def is_complete(self):
        """all required information has been submitted"""
        return not list(self.instance.required)

    def is_valid(self):
        """all fields passed validation and are correct"""
        return not list(self.instance.errors)

    def initiative_is_approved(self):
        """the initiative has been approved"""
        return self.instance.initiative.status == 'approved'

    def initiative_is_submitted(self):
        """the initiative has been submitted"""
        return self.instance.initiative.status in ('submitted', 'approved')

    def initiative_is_not_approved(self):
        """the initiative has not yet been approved"""
        return not self.initiative_is_approved()

    def is_staff(self, user):
        """user is a staff member"""
        return user.is_staff

    def is_owner(self, user):
        """user is the owner"""
        return user == self.instance.owner or user.is_staff

    def should_auto_approve(self):
        return self.instance.auto_approve

    initiate = Transition(
        EmptyState(),
        draft,
        name=_('Create'),
        description=_('The acivity will be created.'),
    )

    auto_submit = Transition(
        [
            draft,
            needs_work,
        ],
        submitted,
        description=_('The acivity will be submitted for review.'),
        automatic=True,
        name=_('Submit'),
        conditions=[is_complete, is_valid],
    )

    reject = Transition(
        AllStates(),
        rejected,
        name=_('Reject'),
        description=_(
            'Reject the activity if it does not fit the programme or '
            'if it does not comply with the rules. '
            'The activity manager can no longer edit the activity '
            'and it will no longer be visible on the platform. '
            'The activity will still be visible in the back '
            'office and will continue to count in the reporting.'
        ),
        automatic=False,
        permission=is_staff,
    )

    submit = Transition(
        [
            draft,
            needs_work,
        ],
        submitted,
        description=_('Submit the activity for approval.'),
        automatic=False,
        name=_('Submit'),
        conditions=[is_complete, is_valid, initiative_is_submitted],
    )

    auto_approve = Transition(
        [
            submitted,
            rejected
        ],
        open,
        name=_('Approve'),
        automatic=True,
        conditions=[should_auto_approve],
        description=_(
            "The activity will be visible in the frontend and people can apply to "
            "the activity."
        ),
    )

    cancel = Transition(
        [
            open,
            succeeded,
        ],
        cancelled,
        name=_('Cancel'),
        description=_(
            'Cancel if the activity will not be executed. '
            'The activity manager can no longer edit the activity '
            'and it will no longer be visible on the platform. '
            'The activity will still be visible in the back office '
            'and will continue to count in the reporting.'
        ),
        automatic=False,
    )

    restore = Transition(
        [
            rejected,
            cancelled,
            deleted,
        ],
        needs_work,
        name=_('Restore'),
        description=_(
            "The activity status is changed to 'Needs work'. "
            "The manager of the activity has to enter a new date and can make changes. "
            "The activity will then be reopened to participants."
        ),
        automatic=False,
    )

    expire = Transition(
        [open, submitted, succeeded],
        expired,
        name=_('Expire'),
        description=_(
            "The activity will be cancelled because no one has signed up for the registration deadline."
        ),
        automatic=True,
    )

    delete = Transition(
        [draft, needs_work],
        deleted,
        name=_('Delete'),
        automatic=False,
        permission=is_owner,
        hide_from_admin=True,
        description=_(
            'Delete the activity if you do not want it to be included in the report. '
            'The activity will no longer be visible on the platform, '
            'but will still be available in the back office.'
        ),
    )

    succeed = Transition(
        open,
        succeeded,
        name=_('Succeed'),
        automatic=True,
    )


class ContributorStateMachine(ModelStateMachine):
    new = State(
        _('new'),
        'new',
        _("The user started a contribution")
    )
    succeeded = State(
        _('succeeded'),
        'succeeded',
        _("The contribution was successful.")
    )
    failed = State(
        _('failed'),
        'failed',
        _("The contribution failed.")
    )

    def is_user(self, user):
        return self.instance.user == user

    initiate = Transition(
        EmptyState(),
        new,
        name=_('initiate'),
        description=_('The contribution was created.')
    )
    fail = Transition(
        (new, succeeded, failed, ),
        failed,
        name=_('fail'),
        description=_("The contribution failed. It will not be visible in reports."),
    )


class ContributionStateMachine(ModelStateMachine):
    new = State(
        _('new'),
        'new',
        _("The user started a contribution")
    )
    succeeded = State(
        _('succeeded'),
        'succeeded',
        _("The contribution was successful.")
    )
    failed = State(
        _('failed'),
        'failed',
        _("The contribution failed.")
    )

    def is_user(self, user):
        return self.instance.user == user

    initiate = Transition(
        EmptyState(),
        new,
        name=_('initiate'),
        description=_('The contribution was created.')
    )

    fail = Transition(
        (new, succeeded, ),
        failed,
        name=_('fail'),
        description=_("The contribution failed. It will not be visible in reports."),
    )

    succeed = Transition(
        new,
        succeeded,
        name=_('succeeded'),
        description=_("The contribution succeeded. It will be visible in reports."),
    )

    reset = Transition(
        [failed, succeeded],
        new,
        name=_('reset'),
        description=_("The contribution is reset."),
    )


@register(Organizer)
class OrganizerStateMachine(ContributorStateMachine):
    succeed = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.failed
        ],
        ContributorStateMachine.succeeded,
        name=_('succeed'),
        description=_('The organizer was successful in setting up the activity.')
    )
    fail = Transition(
        AllStates(),
        ContributorStateMachine.failed,
        name=_('fail'),
        description=_('The organizer failed to set up the activity.')
    )
    reset = Transition(
        [
            ContributorStateMachine.succeeded,
            ContributorStateMachine.failed
        ],
        ContributorStateMachine.new,
        name=_('reset'),
        description=_('The organizer is still busy setting up the activity.')
    )


@register(OrganizerContribution)
class OrganizerContributionStateMachine(ContributionStateMachine):
    pass
