from bluebottle.fsm import transition, TransitionNotPossible
from bluebottle.initiatives.messages import InitiativeClosedOwnerMessage, InitiativeApproveOwnerMessage
from bluebottle.utils.transitions import ReviewTransitions


class InitiativeReviewTransitions(ReviewTransitions):
    def is_complete(self):
        errors = []
        if self.instance.errors:
            errors += self.instance.errors

        if self.instance.required:
            errors += self.instance.required

        if self.instance.organization:
            errors += [error for error in self.instance.organization.required]
            errors += [error for error in self.instance.organization.errors]

        if self.instance.organization_contact:
            errors += [error for error in self.instance.organization_contact.required]
            errors += [error for error in self.instance.organization_contact.errors]

        if errors:
            return errors

    @transition(
        source=[ReviewTransitions.values.draft],
        target=ReviewTransitions.values.submitted,
        conditions=[is_complete]
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
            activity.review_transitions.needs_work(send_messages=False)
            activity.save()

    @transition(
        source=ReviewTransitions.values.submitted,
        target=ReviewTransitions.values.approved,
        messages=[InitiativeApproveOwnerMessage],
        conditions=[is_complete]
    )
    def approve(self):
        for activity in self.instance.activities.all():
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
            activity.review_transitions.close(send_messages=False)
            activity.save()

    @transition(
        source=[ReviewTransitions.values.closed],
        target=ReviewTransitions.values.submitted,
    )
    def reopen(self):
        pass
