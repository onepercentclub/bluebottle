from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm import transition, TransitionNotPossible
from bluebottle.initiatives.messages import InitiativeClosedOwnerMessage, InitiativeApproveOwnerMessage
from bluebottle.utils.transitions import ReviewTransitions


class InitiativeReviewTransitions(ReviewTransitions):
    def is_complete(self):
        errors = [
            _('{} is required').format(self.instance._meta.get_field(field).verbose_name)
            for field in self.instance.required
        ]

        if self.instance.organization:
            errors += [
                _('Organization {} is required').format(
                    self.instance.organization._meta.get_field(field).verbose_name
                ) for field in self.instance.organization.required
            ]

        if self.instance.organization_contact:
            errors += [
                _('Organization Contact {} is required').format(
                    self.instance.organization_contact._meta.get_field(field).verbose_name
                ) for field in self.instance.organization_contact.required
            ]

        if errors:
            return errors

    def is_valid(self):
        errors = [
            error.message for error in self.instance.errors
        ]

        if self.instance.organization:
            errors += [
                error.message for error in self.instance.organization.errors
            ]

        if self.instance.organization_contact:
            errors += [
                error.message for error in self.instance.organization_contact.errors
            ]

        if errors:
            return errors

    @transition(
        source=[ReviewTransitions.values.draft],
        target=ReviewTransitions.values.submitted,
        conditions=[is_complete, is_valid]
    )
    def submit(self):
        for activity in self.instance.activities.all():
            try:
                activity.review_transitions.submit(send_messages=False)
                activity.save()
            except TransitionNotPossible:
                pass

    @transition(
        source=ReviewTransitions.values.needs_work,
        target=ReviewTransitions.values.submitted,
        conditions=[is_complete]
    )
    def resubmit(self):
        for activity in self.instance.activities.all():
            try:
                activity.review_transitions.submit(send_messages=False)
                activity.save()
            except TransitionNotPossible:
                pass

    @transition(
        source=ReviewTransitions.values.submitted,
        target=ReviewTransitions.values.needs_work,
    )
    def needs_work(self):
        for activity in self.instance.activities.all():
            try:
                activity.review_transitions.needs_work(send_messages=False)
                activity.save()
            except TransitionNotPossible:
                pass

    @transition(
        source=ReviewTransitions.values.submitted,
        target=ReviewTransitions.values.approved,
        messages=[InitiativeApproveOwnerMessage],
        conditions=[is_complete]
    )
    def approve(self):
        for activity in self.instance.activities.all():
            # Make sure that activity has the updated initiative status
            activity.initiative.status = self.instance.status
            try:
                activity.review_transitions.approve(send_messages=False)
                activity.save()
            except TransitionNotPossible:
                pass

    @transition(
        source=[
            ReviewTransitions.values.approved,
            ReviewTransitions.values.submitted,
            ReviewTransitions.values.needs_work
        ],
        target=ReviewTransitions.values.closed,
        messages=[InitiativeClosedOwnerMessage],
    )
    def close(self):
        for activity in self.instance.activities.all():
            try:
                # Make sure that activity has the updated initiative status
                activity.initiative.status = self.instance.status
                activity.review_transitions.close(send_messages=False)
                activity.save()
            except TransitionNotPossible:
                pass

    @transition(
        source=[ReviewTransitions.values.closed],
        target=ReviewTransitions.values.draft,
    )
    def reopen(self):
        for activity in self.instance.activities.all():
            try:
                activity.review_transitions.reopen(send_messages=False)
                activity.save()
            except TransitionNotPossible:
                pass
