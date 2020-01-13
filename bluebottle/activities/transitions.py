from django.utils.translation import ugettext_lazy as _
from bluebottle.utils.transitions import ReviewTransitions

from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.fsm import ModelTransitions, transition, TransitionNotPossible


class ActivityReviewTransitions(ReviewTransitions):
    def is_complete(self):
        errors = [
            _('{} is required').format(self.instance._meta.get_field(field).verbose_name)
            for field in self.instance.required
        ]

        if errors:
            return errors

    def is_valid(self):
        errors = [
            error.message[0] for error in self.instance.errors
        ]

        if errors:
            return errors

    def is_activity_manager(self, user):
        return not user or user in [self.instance.initiative.activity_manager, self.instance.owner]

    def can_review(self, user):
        # TODO: Make me smart. Do we want to do this with a auth permission?
        return not user or user.is_staff

    def initiative_is_approved(self):
        if not self.instance.initiative.status == ReviewTransitions.values.approved:
            return _('Please make sure the initiative is approved')

    @transition(
        source=ReviewTransitions.values.draft,
        target=ReviewTransitions.values.submitted,
        conditions=[is_complete, is_valid],
        permissions=[is_activity_manager]
    )
    def submit(self):
        if (
            self.instance.initiative.status == ReviewTransitions.values.approved and
            not self.instance.needs_review
        ):
            self.approve()

    @transition(
        source=[
            ReviewTransitions.values.submitted,
            ReviewTransitions.values.draft,
            ReviewTransitions.values.needs_work
        ],
        target=ReviewTransitions.values.approved,
        conditions=[is_complete, is_valid, initiative_is_approved],
        permissions=[can_review]
    )
    def approve(self):
        try:
            self.instance.transitions.reviewed()
        except TransitionNotPossible:
            pass

    @transition(
        source=[ReviewTransitions.values.submitted],
        target=ReviewTransitions.values.needs_work,
        permissions=[can_review]
    )
    def needs_work(self):
        pass

    @transition(
        source=[
            ReviewTransitions.values.approved,
            ReviewTransitions.values.draft,
            ReviewTransitions.values.submitted,
            ReviewTransitions.values.needs_work
        ],
        target=ReviewTransitions.values.closed,
        permissions=[can_review]
    )
    def close(self):
        self.instance.transitions.close()

    @transition(
        source=ReviewTransitions.values.closed,
        target=ReviewTransitions.values.draft,
        permissions=[can_review]
    )
    def resubmit(self):
        if self.instance.status != ActivityTransitions.values.in_review:
            self.instance.transitions.resubmit()

    @transition(
        source=[
            ReviewTransitions.values.draft,
            ReviewTransitions.values.submitted,
            ReviewTransitions.values.needs_work
        ],
        target=ReviewTransitions.values.closed,
        permissions=[is_activity_manager]
    )
    def delete(self):
        self.instance.transitions.delete()


class ActivityTransitions(ModelTransitions):
    class values(DjangoChoices):
        in_review = ChoiceItem('in_review', _('in review'))
        open = ChoiceItem('open', _('open'))
        succeeded = ChoiceItem('succeeded', _('succeeded'))
        closed = ChoiceItem('closed', _('closed'))
        deleted = ChoiceItem('deleted', _('deleted'))

    default = values.in_review

    def initiative_is_approved(self):
        if not self.instance.initiative.status == 'approved':
            return _('Please make sure the initiative is approved')

    def can_approve(self, user):
        # TODO: Make me smart. Do we want to do this with a auth permission?
        return not user or user.is_staff

    def is_system(self, user):
        # Only system and admin users. Not api users.
        return not user

    @transition(
        source=values.closed,
        target=values.in_review,
        permissions=[can_approve],
    )
    def reopen(self):
        pass

    @transition(
        source=[
            values.closed,
            values.deleted
        ],
        target=values.in_review,
        permissions=[can_approve],
    )
    def resubmit(self):
        if self.instance.review_status == ActivityReviewTransitions.values.closed:
            self.instance.review_transitions.resubmit()

    @transition(
        source=[values.in_review],
        target=values.deleted,
        permissions=[is_system]
    )
    def delete(self):
        pass


class ContributionTransitions(ModelTransitions):
    class values(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        succeeded = ChoiceItem('succeeded', _('succeeded'))
        failed = ChoiceItem('failed', _('failed'))
        closed = ChoiceItem('closed', _('closed'))

    def is_user(self, user):
        return self.instance.user == user

    def can_review(self, user):
        # TODO: Make me smart. Do we want to do this with a auth permission?
        return not user or user.is_staff

    def is_activity_manager(self, user):
        return user in [
            self.instance.activity.initiative.activity_manager,
            self.instance.activity.owner]

    @transition(
        source='*',
        target=values.closed,
        permissions=[can_review]
    )
    def close(self):
        self.instance.transitions.close()
