from django.conf.urls import url
from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.template import loader
from django.template.response import TemplateResponse

from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.fsm.forms import StateMachineModelForm
from bluebottle.utils.forms import TransitionConfirmationForm


def log_action(obj, user, change_message='Changed', action_flag=CHANGE):
    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=unicode(obj),
        action_flag=action_flag,
        change_message=change_message
    )


class StateMachineAdminMixin(object):
    form = StateMachineModelForm

    def get_transition(self, instance, name, field_name):
        transitions = getattr(instance, field_name).all_transitions
        for transition in transitions:
            if transition.name == name:
                return transition

    def transition(self, request, pk, field_name, transition_name, send_messages=True):
        link = reverse(
            'admin:{}_{}_change'.format(
                self.model._meta.app_label, self.model._meta.model_name
            ),
            args=(pk, )
        )

        # perform actual check for change permission. using self.model
        permission = '{}.change_{}'.format(
            self.model._meta.app_label, self.model._meta.model_name
        )
        if not request.user.has_perm(permission):
            messages.error(request, 'Missing permission: {}'.format(permission))
            return HttpResponseRedirect(link)

        instance = self.model.objects.get(pk=pk)
        form = TransitionConfirmationForm(request.POST)

        state_machine = getattr(instance, field_name)
        transition = state_machine.transitions[transition_name]

        if 'confirm' in request.POST and request.POST['confirm']:
            if form.is_valid():
                send_messages = form.cleaned_data['send_messages']

                try:
                    getattr(state_machine, transition_name)(
                        send_messages=send_messages,
                        user=request.user,
                        save=True
                    )

                    log_action(
                        instance,
                        request.user,
                        'Changed status to {}'.format(transition.target.value)
                    )

                    return HttpResponseRedirect(link)
                except TransitionNotPossible:
                    errors = transition.errors(instance.transitions)
                    if errors:
                        template = loader.get_template(
                            'admin/transition_errors.html'
                        )
                        error_message = template.render({'errors': errors})
                    else:
                        error_message = 'Transition not allowed: {}'.format(transition.name)

                    messages.error(request, error_message)

                    return HttpResponseRedirect(link)

        notifications = []
        transition_messages = transition.options.get('messages', [])

        for message in transition_messages:
            notifications += message(instance).get_messages()

        context = dict(
            self.admin_site.each_context(request),
            title=TransitionConfirmationForm.title,
            action=transition.field,
            opts=self.model._meta,
            obj=instance,
            pk=instance.pk,
            form=form,
            source=instance.status,
            notifications=notifications,
            target=transition.target.name,
        )

        return TemplateResponse(
            request, 'admin/transition_confirmation.html', context
        )

    def get_urls(self):
        urls = super(StateMachineAdminMixin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<pk>.+)/transition/(?P<field_name>.+)/(?P<transition_name>.+)$',
                self.admin_site.admin_view(self.transition),
                name='{}_{}_state_transition'.format(
                    self.model._meta.app_label, self.model._meta.model_name
                ),
            ),
        ]
        return custom_urls + urls


class StateMachineAdmin(StateMachineAdminMixin, admin.ModelAdmin):
    pass
