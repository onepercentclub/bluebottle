from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.state import ModelStateMachine, State, EmptyState, Transition
from bluebottle.initiatives.effects import ApproveActivity

from bluebottle.initiatives.models import Initiative


class ReviewStateMachine(ModelStateMachine):
    field = 'status'
    model = Initiative

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

    initiate = Transition(EmptyState(), draft)

    submit = Transition(
        draft,
        submitted,
        name=_('Submit'),
        conditions=[is_complete],
        automatic=False
    )
    approve = Transition(
        submitted,
        approved,
        name=_('Approve'),
        conditions=[is_complete],
        automatic=False,
        effects=[ApproveActivity]
    )
    close = Transition(
        (draft, submitted, approved),
        closed,
        name=_('Close'),
        automatic=False
    )
    reopen = Transition(
        closed,
        draft,
        name=_('Reopen'),
        automatic=False
    )
