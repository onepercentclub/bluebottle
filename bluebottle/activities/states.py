from django.utils.translation import gettext_lazy as _

from bluebottle.activities.models import Organizer, EffortContribution
from bluebottle.fsm.state import ModelStateMachine, State, EmptyState, AllStates, Transition, register


class ActivityStateMachine(ModelStateMachine):
    draft = State(
        _('draft'),
        'draft',
        _('The activity has been created, but not yet completed. An activity manager is still editing the activity.')
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
            'The activity cannot be edited by an activity manager.'
        )
    )
    deleted = State(
        _('deleted'),
        'deleted',
        _(
            'The activity has been removed. The activity does not appear on '
            'the platform and does not count in the report. '
            'The activity cannot be edited by an activity manager.'
        ),
    )
    cancelled = State(
        _('cancelled'),
        'cancelled',
        _(
            'The activity is not executed. The activity does not appear on the platform, '
            'but counts in the report. The activity cannot be edited by an activity manager.'
        ),
    )

    expired = State(
        _('expired'),
        'expired',
        _(
            'The activity has ended, but did have any contributions . The activity does not appear on the platform, '
            'but counts in the report. The activity cannot be edited by an activity manager.'
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
        return self.instance.initiative_id and self.instance.initiative.status == 'approved'

    def initiative_is_submitted(self):
        """the initiative has been submitted"""
        return not self.instance.initiative_id or self.instance.initiative.status in ('submitted', 'approved')

    def initiative_is_not_approved(self):
        """the initiative has not yet been approved"""
        return self.initiative_is_approved()

    def is_staff(self, user):
        """user is a staff member"""
        return user.is_staff

    def is_owner(self, user):
        """user is the owner"""
        return (
            user == self.instance.owner or
            (
                self.instance.initiative and (
                    user == self.instance.initiative.owner or
                    user in self.instance.initiative.activity_managers.all()
                )
            ) or
            user.is_staff
        )

    def should_auto_approve(self):
        """the activity should be approved automatically"""
        return self.instance.auto_approve

    initiate = Transition(
        EmptyState(),
        draft,
        name=_('Create'),
        description=_('The activity will be created.'),
    )

    auto_submit = Transition(
        [
            draft,
            needs_work,
        ],
        submitted,
        description=_('The activity will be submitted for review.'),
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
            'The activity manager can no longer edit the activity.'
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
        description=_((
            'After submitting your activity, it will be reviewed by a platform administrator.'
            'You cannot make changes until this process has completed.'
        )),
        automatic=False,
        name=_('Submit'),
        permission=is_owner,
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

    approve = Transition(
        [
            submitted,
            rejected
        ],
        open,
        name=_('Approve'),
        automatic=False,
        permissions=[is_staff],
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
            'An activity manager can no longer edit the activity '
            'and it will no longer be visible on the platform. '
            'The activity will still be visible in the back office '
            'and will continue to count in the reporting.'
        ),
        description_front_end=_(
            'The activity ends and people no longer register. All current participants will fail too.'
        ),
        permission=is_owner,
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
            "Then you can make changes to the activity and submit it again."
        ),
        description_front_end=_(
            "The activity will be set to the status ‘Needs work’. "
            "Then you can make changes to the activity and submit it again."
        ),
        automatic=False,
        permission=is_owner
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
        description_front_end=_('Delete the activity. You will not be able to retrieve it afterwards.')
    )

    succeed = Transition(
        open,
        succeeded,
        name=_('Succeed'),
        automatic=True,
    )


class ContributorStateMachine(ModelStateMachine):
    new = State(
        _('New'),
        'new',
        _("The user started a contribution")
    )
    succeeded = State(
        _('Succeeded'),
        'succeeded',
        _("The contribution was successful.")
    )
    failed = State(
        _('Failed'),
        'failed',
        _("The contribution failed.")
    )

    def is_user(self, user):
        return self.instance.user == user

    initiate = Transition(
        EmptyState(),
        new,
        name=_('Initiate'),
        description=_('The contribution was created.')
    )
    fail = Transition(
        (new, succeeded, failed,),
        failed,
        name=_('Fail'),
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
        [new, succeeded],
        failed,
        name=_('fail'),
        description=_("The contribution failed. It will not be visible in reports."),
    )

    succeed = Transition(
        [new, failed],
        succeeded,
        name=_("succeed"),
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


@register(EffortContribution)
class EffortContributionStateMachine(ContributionStateMachine):
    pass
