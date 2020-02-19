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

    submit = draft.to(submitted, conditions=[is_complete])
    approve = submitted.to(
        approved, conditions=[is_complete]
    )
    close = (draft | submitted | approved).to(closed)
    reopen = closed.to(draft)
