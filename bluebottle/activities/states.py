from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.models import Organizer
from bluebottle.fsm.effects import Effect, TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.state import ModelStateMachine, State, EmptyState, AllStates, Transition


class CreateOrganizer(Effect):
    "Create an organizer for the activity"
    post_save = True

    def execute(self, **kwargs):
        Organizer.objects.get_or_create(
            activity=self.instance,
            defaults={'user': self.instance.owner}
        )

    def __unicode__(self):
        return unicode(_('Create organizer'))


class ActivityStateMachine(ModelStateMachine):
    draft = State(
        _('draft'),
        'draft',
        _('The activity is created by the user.')
    )
    submitted = State(
        _('submitted'),
        'submitted',
        _('The activity is complete and needs to be review.')
    )
    needs_work = State(
        _('needs work'),
        'needs_work',
        _('The activity has not been approved by the reviewer and needs to be edited.')
    )
    rejected = State(
        _('rejected'),
        'rejected',
        _('The activity has been rejected by the reviewer.')
    )
    deleted = State(
        _('deleted'),
        'deleted',
        _('The activity is deleted by the initiator.')
    )
    open = State(
        _('open'),
        'open',
        _('The activity is open, and accepting contributions.')
    )
    succeeded = State(
        _('succeeded'),
        'succeeded',
        _('The activity has ended successfully.')
    )
    closed = State(
        _('closed'),
        'closed',
        _('The activity was unsuccessfull and has been closed.')
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
        return user == self.instance.owner

    initiate = Transition(
        EmptyState(),
        draft,
        name=_('Initiate'),
        effects=[CreateOrganizer]
    )

    submit = Transition(
        [draft, needs_work],
        submitted,
        automatic=False,
        name=_('Submit'),
        conditions=[is_complete, is_valid, initiative_is_submitted],
        effects=[
            TransitionEffect('approve', conditions=[initiative_is_approved])
        ]
    )

    approve = Transition(
        [
            draft,
            submitted,
            rejected,
            needs_work
        ],
        open,
        automatic=False,
        permission=is_staff,
        name=_('Approve'),
        effects=[
            RelatedTransitionEffect('organizer', 'succeed')
        ]
    )

    reject = Transition(
        AllStates(),
        rejected,
        name=_('Reject'),
        automatic=False,
        permission=is_staff,
        effects=[RelatedTransitionEffect('organizer', 'fail')]
    )

    restore = Transition(
        rejected,
        draft,
        name=_('Restore'),
        automatic=False,
        permission=is_staff,
        effects=[RelatedTransitionEffect('organizer', 'succeed')]
    )

    close = Transition(
        open,
        closed,
        name=_('Close'),
        automatic=True,
        effects=[RelatedTransitionEffect('organizer', 'fail')]
    )

    restore = Transition(
        [rejected, closed, deleted],
        draft,
        name=_('Restore'),
        automatic=False,
        permission=is_staff,
        effects=[RelatedTransitionEffect('organizer', 'reset')]
    )

    delete = Transition(
        [draft, needs_work, submitted],
        deleted,
        name=_('Delete'),
        automatic=False,
        permission=is_owner,
        effects=[RelatedTransitionEffect('organizer', 'fail')]
    )

    succeed = Transition(
        [open],
        succeeded,
        name=_('Succeed'),
        automatic=True,
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
    closed = State(
        _('closed'),
        'closed',
        _("The contribution is closed unsuccessfully.")
    )

    def is_user(self, user):
        return self.instance.user == user

    initiate = Transition(EmptyState(), new)
    close = Transition(
        (new, succeeded, failed, ),
        closed,
        name=_('close'),
        description=_("Close the contribution. It will not be visible in reports."),
    )


class OrganizerStateMachine(ContributionStateMachine):
    model = Organizer

    succeed = Transition(
        [
            ContributionStateMachine.new,
            ContributionStateMachine.failed
        ],
        ContributionStateMachine.succeeded,
        name=_('succeed'),
        description=_('The organizer was successful in setting up the activity.')
    )
    fail = Transition(
        AllStates(),
        ContributionStateMachine.failed,
        name=_('fail'),
        description=_('The organizer failed to set up the activity.')
    )
    reset = Transition(
        [
            ContributionStateMachine.succeeded,
            ContributionStateMachine.failed
        ],
        ContributionStateMachine.new,
        name=_('reset'),
        description=_('The organizer is still busy setting up the activity.')
    )
