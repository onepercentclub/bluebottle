from bluebottle.fsm import transition, TransitionNotPossible
from bluebottle.initiatives.messages import InitiativeClosedOwnerMessage, InitiativeApproveOwnerMessage
from bluebottle.utils.transitions import ReviewTransitions


class InitiativeReviewTransitions(ReviewTransitions):
    def is_complete(self):
        from bluebottle.initiatives.serializers import InitiativeValidationSerializer
        from bluebottle.organizations.serializers import (
            OrganizationContactValidationSerializer, OrganizationValidationSerializer
        )

        serializer = InitiativeValidationSerializer(instance=self.instance)
        if not serializer.is_valid():
            return serializer.errors

        serializer = OrganizationValidationSerializer(instance=self.instance.organization)
        if self.instance.organization and not serializer.is_valid():
            return serializer.errors

        serializer = OrganizationContactValidationSerializer(instance=self.instance.organization_contact)
        if self.instance.organization_contact and not serializer.is_valid():
            return serializer.errors

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
