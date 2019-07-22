from django.forms.models import model_to_dict
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.fsm import ModelTransitions, transition


class ActivityTransitions(ModelTransitions):
    class values(DjangoChoices):
        draft = ChoiceItem('draft', _('draft'))
        open = ChoiceItem('open', _('open'))
        succeeded = ChoiceItem('succeeded', _('succeeded'))
        closed = ChoiceItem('closed', _('closed'))

    default = values.draft

    def is_complete(self):
        serializer_class = import_string(self.serializer)
        serializer = serializer_class(
            data=model_to_dict(self.instance)
        )
        if not serializer.is_valid():
            return [unicode(error) for errors in serializer.errors.values() for error in errors]

    def initiative_is_approved(self):
        if not self.instance.initiative.status == 'approved':
            return _('Please make sure the initiative is approved')

    @transition(
        source=values.draft,
        target=values.open,
        conditions=[is_complete, initiative_is_approved],
    )
    def open(self):
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
