from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from bluebottle.utils.transitions import ReviewTransitions

from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.fsm import ModelTransitions, transition


class ActivityReviewTransitions(ReviewTransitions):
    def is_complete(self):
        serializer_class = import_string(self.instance.complete_serializer)

        serializer = serializer_class(instance=self.instance)

        if not serializer.is_valid():
            return serializer.errors

    @transition(
        source=ReviewTransitions.values.draft,
        target=ReviewTransitions.values.submitted,
        conditions=[is_complete]
    )
    def submit(self):
        if (
            self.instance.initiative.status == ReviewTransitions.values.approved and
            not self.instance.needs_review
        ):
            self.approve()

    @transition(
        source=[ReviewTransitions.values.submitted, ReviewTransitions.values.draft],
        target=ReviewTransitions.values.approved,
        conditions=[is_complete]
    )
    def approve(self):
        self.instance.transitions.reviewed()

    @transition(
        source=[
            ReviewTransitions.values.approved,
            ReviewTransitions.values.submitted,
            ReviewTransitions.values.needs_work
        ],
        target=ReviewTransitions.values.closed
    )
    def close(self):
        pass


class ActivityTransitions(ModelTransitions):
    class values(DjangoChoices):
        in_review = ChoiceItem('in_review', _('In review'))
        open = ChoiceItem('open', _('open'))
        succeeded = ChoiceItem('succeeded', _('succeeded'))
        closed = ChoiceItem('closed', _('closed'))

    default = values.in_review

    def initiative_is_approved(self):
        if not self.instance.initiative.status == 'approved':
            return _('Please make sure the initiative is approved')

    @transition(
        source=values.in_review,
        target=values.open,
    )
    def reviewed(self):
        pass

    @transition(
        source=values.closed,
        target=values.in_review,
    )
    def reopen(self, **kwargs):
        pass


class ContributionTransitions(ModelTransitions):
    class values(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        succeeded = ChoiceItem('succeeded', _('succeeded'))
        failed = ChoiceItem('failed', _('failed'))

    def is_user(self, user):
        return self.instance.user == user

    def is_activity_manager(self, user):
        return self.instance.activity.initiative.activity_manager == user
