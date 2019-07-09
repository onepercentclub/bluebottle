from django.utils.translation import ugettext_lazy as _

from djchoices.choices import DjangoChoices, ChoiceItem

from bluebottle.fsm import ModelTransitions


class ActivityTransitions(ModelTransitions):
    class values(DjangoChoices):
        draft = ChoiceItem('draft', _('draft'))
        open = ChoiceItem('open', _('open'))
        full = ChoiceItem('full', _('full'))
        running = ChoiceItem('running', _('running'))
        done = ChoiceItem('done', _('done'))
        closed = ChoiceItem('closed', _('closed'))

    default = values.draft


class ContributionTransitions(ModelTransitions):
    class values(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        success = ChoiceItem('success', _('success'))
        failed = ChoiceItem('success', _('success'))

    def is_user(self, user):
        return self.instance.user == user

    def is_activity_manager(self, user):
        return self.instance.activity.initiative.activity_manager == user
