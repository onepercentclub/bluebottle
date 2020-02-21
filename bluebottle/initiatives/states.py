from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.state import ProxiedStateMachine, State, EmptyState


class ReviewStateMachine(ProxiedStateMachine):
    draft = State(_('draft'), 'draft')
    submitted = State(_('submitted'), 'submitted')
    needs_work = State(_('needs work'), 'needs_work')
    approved = State(_('approved'), 'approved')
    closed = State(_('closed'), 'closed')
    deleted = State(_('deleted'), 'deleted')

    def is_complete(self):
        return not list(self.instance.required)

    def is_valid(self):
        return not list(self.instance.errors)

    initiate = EmptyState().to(draft)

    submit = draft.to(submitted, name=_('Submit'), conditions=[is_complete], automatic=False)
    approve = submitted.to(
        approved, name=_('Approve'), conditions=[is_complete], automatic=False
    )
    close = (draft | submitted | approved).to(closed, name=_('Close'), automatic=False)
    reopen = closed.to(draft, name=_('Reopen'), automatic=False)
