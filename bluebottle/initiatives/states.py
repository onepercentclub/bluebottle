from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.state import ModelStateMachine, State, EmptyState, Transition, AllStates
from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.initiatives.effects import (
    ApproveActivities, RejectActivities
)
from bluebottle.initiatives.messages import InitiativeRejectedOwnerMessage, InitiativeApprovedOwnerMessage

from bluebottle.initiatives.models import Initiative

from bluebottle.notifications.effects import NotificationEffect


class ReviewStateMachine(ModelStateMachine):
    field = 'status'
    model = Initiative

    draft = State(
        _('draft'),
        'draft',
        _('The initiative is created by the user.')
    )
    submitted = State(
        _('submitted'),
        'submitted',
        _('The initiative is complete and ready to be reviewed.')
    )
    needs_work = State(
        _('needs work'),
        'needs_work',
        _('The initiative needs to be edited.')
    )
    rejected = State(
        _('rejected'),
        'rejected',
        _('The initiative is rejected by the reviewer and not visible on the platform.')
    )
    approved = State(
        _('approved'),
        'approved',
        _('The initiative is approved by the reviewer and is visible on the platform.')
    )

    def is_complete(self):
        """The initiative is complete"""
        if self.instance.organization and list(self.instance.organization.required):
            return False

        if self.instance.organization_contact and list(self.instance.organization_contact.required):
            return False

        return not list(self.instance.required)

    def is_valid(self):
        """The initiative is valid"""
        if self.instance.organization and list(self.instance.organization.errors):
            return False

        if self.instance.organization_contact and list(self.instance.organization_contact.errors):
            return False

        return not list(self.instance.errors)

    def is_staff(self, user):
        return user.is_staff

    initiate = Transition(EmptyState(), draft)

    submit = Transition(
        [draft, needs_work],
        submitted,
        name=_('Submit'),
        description=_("The initiative will be submitted for review."),
        conditions=[is_complete, is_valid],
        automatic=False,
        effects=[
            RelatedTransitionEffect('activities', 'submit')
        ]
    )

    approve = Transition(
        submitted,
        approved,
        name=_('Approve'),
        description=_("The initiative will be approved and go online."),
        conditions=[is_complete, is_valid],
        automatic=False,
        permission=is_staff,
        effects=[
            ApproveActivities,
            NotificationEffect(InitiativeApprovedOwnerMessage)
        ]
    )

    request_changes = Transition(
        submitted,
        needs_work,
        name=_('Request Changes'),
        description=_("The initiative needs work. The initiator will be able to edit it again."),
        conditions=[],
        automatic=False,
    )

    reject = Transition(
        AllStates(),
        rejected,
        name=_('Reject'),
        description=_("The initiative will be rejected. "
                      "The initiator will not be able to edit it and it won't be visible on the platform"),
        automatic=False,
        permission=is_staff,
        effects=[
            RejectActivities,
            NotificationEffect(InitiativeRejectedOwnerMessage)
        ]
    )

    restore = Transition(
        rejected,
        draft,
        name=_('Restore'),
        description=_("The initiative will be restored. The initiator will be able to edit it again."),
        automatic=False,
        permission=is_staff,
    )
