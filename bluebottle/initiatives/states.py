from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.state import ModelStateMachine, State, EmptyState, Transition, AllStates
from bluebottle.initiatives.effects import ApproveActivities, RejectActivities
from bluebottle.initiatives.messages import InitiativeRejectedOwnerMessage, InitiativeApprovedOwnerMessage

from bluebottle.initiatives.models import Initiative

from bluebottle.notifications.effects import NotificationEffect


class ReviewStateMachine(ModelStateMachine):
    field = 'status'
    model = Initiative

    draft = State(_('draft'), 'draft')
    submitted = State(_('submitted'), 'submitted')
    needs_work = State(_('needs work'), 'needs_work')
    approved = State(_('approved'), 'approved')
    rejected = State(_('rejected'), 'rejected')

    def is_complete(self):
        if self.instance.organization and list(self.instance.organization.required):
            return False

        if self.instance.organization_contact and list(self.instance.organization_contact.required):
            return False

        return not list(self.instance.required)

    def is_valid(self):
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
        conditions=[is_complete, is_valid],
        automatic=False
    )
    approve = Transition(
        submitted,
        approved,
        name=_('Approve'),
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
        conditions=[],
        automatic=False,
    )
    reject = Transition(
        AllStates(),
        rejected,
        name=_('Reject'),
        automatic=False,
        permission=is_staff,
        effects=[RejectActivities, NotificationEffect(InitiativeRejectedOwnerMessage)]
    )
    accept = Transition(
        rejected,
        draft,
        name=_('Accept'),
        automatic=False,
        permission=is_staff,
    )
