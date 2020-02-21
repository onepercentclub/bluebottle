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

    def initiative_is_approved(self):
        return self.instance.initiative.status == 'approved'

    def initiative_is_not_approved(self):
        return not self.initiative_is_approved()

    initiate = EmptyState().to(draft, name=_('Initiate'))

    submit = draft.to(submitted, name=_('Submit'), conditions=[is_complete])
    approve = submitted.to(
        approved,
        conditions=[is_complete, initiative_is_approved]
    )
    close = (draft | submitted | approved).to(closed, automatic=False)
    close_because_of_initiative = (draft | submitted | approved).to(
        closed, conditions=[initiative_is_not_approved]
    )
    reopen = closed.to(draft, automatic=False)


class ActivityStateMachine(ProxiedStateMachine):
    in_review = State(_('in review'), 'in_review')
    open = State(_('open'), 'open')
    succeeded = State(_('succeeded'), 'succeeded')
    closed = State(_('closed'), 'closed')

    def is_approved(self):
        return self.instance.review_status == ReviewStateMachine.approved.value

    def is_not_approved(self):
        return not self.is_approved

    initiate = EmptyState().to(in_review)

    approve = in_review.to(open, conditions=[is_approved])
    unreview = (open | succeeded | closed).to(
        in_review, conditions=[is_not_approved]
    )


class ContributionStateMachine(ProxiedStateMachine):
    new = State(_('new'), 'new')
    succeeded = State(_('succeeded'), 'succeeded')
    failed = State(_('failed'), 'failed')
    closed = State(_('closed'), 'closed')

    def activity_is_closed(self):
        return self.instance.activity.review_status in (
            ReviewStateMachine.closed.value, ReviewStateMachine.deleted.value
        )

    def activity_is_succeeded(self):
        return self.instance.activity.status == ActivityStateMachine.succeeded.value

    def activity_is_open(self):
        return self.instance.activity.status == ActivityStateMachine.open.value

    initiate = EmptyState().to(new)

    close = (new | succeeded | failed).to(
        closed, conditions=[activity_is_closed]
    )


class OrganizerStateMachine(ContributionStateMachine):
    def activity_is_approved(self):
        return self.instance.activity.review_status == ReviewStateMachine.approved.value

    def activity_is_not_approved(self):
        return not self.activity_is_approved

    succeed = (ContributionStateMachine.new | ContributionStateMachine.failed).to(
        ContributionStateMachine.succeeded,
        conditions=[activity_is_approved]
    )

    reset = (ContributionStateMachine.succeeded | ContributionStateMachine.closed).to(
        ContributionStateMachine.new,
        conditions=[activity_is_not_approved]
    )
