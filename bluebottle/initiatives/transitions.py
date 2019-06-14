from django.forms.models import model_to_dict
from django.utils.translation import ugettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.fsm import ModelTransitions, transition, TransitionNotAllowed
from bluebottle.initiatives.messages import InitiativeClosedOwnerMessage, InitiativeApproveOwnerMessage


class InitiativeTransitions(ModelTransitions):
    class values(DjangoChoices):
        draft = ChoiceItem('draft', _('draft'))
        submitted = ChoiceItem('submitted', _('submitted'))
        needs_work = ChoiceItem('needs_work', _('needs work'))
        approved = ChoiceItem('approved', _('approved'))
        closed = ChoiceItem('closed', _('closed'))

    default = values.draft

    def is_complete(instance):
        from bluebottle.initiatives.serializers import InitiativeSubmitSerializer

        serializer = InitiativeSubmitSerializer(
            data=model_to_dict(instance)
        )
        if not serializer.is_valid():
            return [unicode(error) for errors in serializer.errors.values() for error in errors]

    @transition(
        source=values.draft,
        target=values.submitted,
        conditions=[is_complete],
        custom={'button_name': _('submit')}
    )
    def submit(self, instance):
        pass

    @transition(
        source=values.needs_work,
        target=values.submitted,
        conditions=[is_complete],
        custom={'button_name': _('resubmit')}
    )
    def resubmit(self, instance):
        pass

    @transition(
        source=values.submitted,
        target=values.needs_work,
        custom={'button_name': _('needs work')}
    )
    def needs_work(self, instance):
        pass

    @transition(
        source=values.submitted,
        target=values.approved,
        messages=[InitiativeApproveOwnerMessage],
        conditions=[is_complete],
        custom={'button_name': _('approve')}
    )
    def approve(self, instance):
        for activity in instance.activities.filter(status='draft'):
            activity.initiative = self
            try:
                activity.transitions.open()
                activity.save()
            except TransitionNotAllowed:
                pass

    @transition(
        source=[values.approved, values.submitted, values.needs_work],
        target=values.closed,
        messages=[InitiativeClosedOwnerMessage],
        custom={'button_name': _('close')}
    )
    def close(self, instance):
        pass

    @transition(
        source=[values.approved, values.closed],
        target=values.submitted,
        conditions=[is_complete],
        custom={'button_name': _('re-open')}
    )
    def reopen(self, instance):
        pass
