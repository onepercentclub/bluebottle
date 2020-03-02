from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.state import ModelStateMachine, State, EmptyState, Transition
from bluebottle.fsm.effects import Effect, TransitionEffect, RelatedTransitionEffect

from bluebottle.activities.models import Organizer, Activity


class CreateOrganizer(Effect):
    post_save = True

    def execute(self):
        Organizer.objects.get_or_create(activity=self.instance)


class ReviewStateMachine(ModelStateMachine):
    field = 'review_status'
    name = 'review_states'

    model = Activity

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

    def initiative_is_approved(self):
        return self.instance.initiative.status == 'approved'

    def initiative_is_not_approved(self):
        return not self.initiative_is_approved()

    initiate = Transition(
        EmptyState(),
        draft,
        name=_('Initiate')
    )

    submit = Transition(
        draft,
        submitted,
        name=_('Submit'),
        effects=[
            TransitionEffect('approve', 'review_states', conditions=[initiative_is_approved])
        ]
    )

    approve = Transition(
        (draft, submitted, ),
        approved,
        name=_('Approve'),
        automatic=False,
        effects=[
            TransitionEffect('approve'),
            RelatedTransitionEffect('organizer', 'succeed')
        ]
    )

    close = Transition(
        (draft, submitted, approved, ),
        closed,
        name=_('Close'),
        automatic=False,
        effects=[TransitionEffect('review', 'states'), RelatedTransitionEffect('organizer', 'closed')]
    )
    close_because_of_initiative = Transition(
        (draft, submitted, approved, ),
        closed,
    )
    reopen = Transition(
        closed,
        draft,
        name=_('Reopen'),
        automatic=False,
        effects=[RelatedTransitionEffect('organizers', 'reset')]
    )


class ActivityStateMachine(ModelStateMachine):
    in_review = State(_('in review'), 'in_review')
    open = State(_('open'), 'open')
    succeeded = State(_('succeeded'), 'succeeded')
    closed = State(_('closed'), 'closed')

    initiate = Transition(
        EmptyState(),
        in_review,
        effects=[CreateOrganizer]
    )

    approve = Transition(in_review, open)
    unreview = Transition((open, succeeded, closed, ), in_review)


class ContributionStateMachine(ModelStateMachine):
    new = State(_('new'), 'new')
    succeeded = State(_('succeeded'), 'succeeded')
    failed = State(_('failed'), 'failed')
    closed = State(_('closed'), 'closed')

    initiate = Transition(EmptyState(), new)
    close = Transition(
        (new, succeeded, failed, ),
        closed
    )


class OrganizerStateMachine(ContributionStateMachine):
    model = Organizer

    succeed = Transition(
        (ContributionStateMachine.new, ContributionStateMachine.failed, ),
        ContributionStateMachine.succeeded
    )

    reset = Transition(
        (ContributionStateMachine.succeeded, ContributionStateMachine.closed, ),
        ContributionStateMachine.new,
    )
