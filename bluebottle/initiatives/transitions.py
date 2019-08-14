from django.forms.models import model_to_dict
from django.utils.translation import ugettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.fsm import ModelTransitions, transition, TransitionNotPossible
from bluebottle.initiatives.messages import InitiativeClosedOwnerMessage, InitiativeApproveOwnerMessage


class InitiativeTransitions(ModelTransitions):
    class values(DjangoChoices):
        draft = ChoiceItem('draft', _('draft'))
        submitted = ChoiceItem('submitted', _('submitted'))
        needs_work = ChoiceItem('needs_work', _('needs work'))
        approved = ChoiceItem('approved', _('approved'))
        closed = ChoiceItem('closed', _('closed'))

    default = values.draft

    def is_complete(self):
        from bluebottle.initiatives.serializers import InitiativeSubmitSerializer

        data = model_to_dict(self.instance)
        if self.instance.organization:
            data['organization'] = model_to_dict(self.instance.organization)
        if self.instance.organization_contact:
            data['organization_contact'] = model_to_dict(self.instance.organization_contact)

        serializer = InitiativeSubmitSerializer(data=data)

        if not serializer.is_valid():
            return [unicode(error) for errors in serializer.errors.values() for error in errors]

    @transition(
        source=values.draft,
        target=values.submitted,
        conditions=[is_complete],
    )
    def submit(self):
        pass

    @transition(
        source=values.needs_work,
        target=values.submitted,
        conditions=[is_complete],
    )
    def resubmit(self):
        pass

    @transition(
        source=values.submitted,
        target=values.needs_work,
    )
    def needs_work(self):
        pass

    @transition(
        source=values.submitted,
        target=values.approved,
        messages=[InitiativeApproveOwnerMessage],
        conditions=[is_complete],
    )
    def approve(self):
        for activity in self.instance.activities.filter(status='draft'):
            activity.initiative = self.instance
            try:
                activity.transitions.open()
                activity.save()
            except TransitionNotPossible:
                pass

    @transition(
        source=[values.approved, values.submitted, values.needs_work],
        target=values.closed,
        messages=[InitiativeClosedOwnerMessage],
    )
    def close(self):
        pass

    @transition(
        source=[values.closed],
        target=values.submitted,
        conditions=[is_complete],
    )
    def reopen(self):
        pass
